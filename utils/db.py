"""База данных PostgreSQL"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "")

DEFAULT_CATEGORIES_EXPENSE = [
    "Еда и продукты", "Кафе и рестораны", "Транспорт", "Такси",
    "Коммунальные услуги", "Связь и интернет", "Одежда",
    "Здоровье и аптека", "Развлечения", "Образование",
    "Путешествия", "Дом и ремонт", "Техника", "Подарки",
    "Бизнес-расходы", "Прочее"
]

DEFAULT_CATEGORIES_INCOME = [
    "Зарплата", "Фриланс", "Бизнес", "Аренда",
    "Инвестиции", "Подарок", "Возврат долга", "Прочее"
]


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("❌ DATABASE_URL не задана!")
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id          SERIAL PRIMARY KEY,
                    user_id     BIGINT NOT NULL,
                    type        TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    amount      NUMERIC(15, 2) NOT NULL,
                    currency    TEXT NOT NULL DEFAULT 'ARS',
                    category    TEXT,
                    description TEXT,
                    raw_text    TEXT,
                    created_at  TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_date ON transactions(user_id, created_at)")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id         SERIAL PRIMARY KEY,
                    user_id    BIGINT NOT NULL,
                    category   TEXT NOT NULL,
                    amount     NUMERIC(15, 2) NOT NULL,
                    currency   TEXT NOT NULL DEFAULT 'ARS',
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, category)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id         BIGINT PRIMARY KEY,
                    budgets_enabled BOOLEAN DEFAULT FALSE,
                    onboarded       BOOLEAN DEFAULT FALSE,
                    created_at      TIMESTAMP DEFAULT NOW()
                )
            """)
            # Пользовательские категории
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_categories (
                    id         SERIAL PRIMARY KEY,
                    user_id    BIGINT NOT NULL,
                    name       TEXT NOT NULL,
                    type       TEXT NOT NULL DEFAULT 'expense' CHECK(type IN ('expense', 'income', 'both')),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, name)
                )
            """)
        conn.commit()


# ── Транзакции ────────────────────────────────────────────────────────────────

def save_transaction(user_id, tx_type, amount, currency, category, description, raw_text):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transactions (user_id, type, amount, currency, category, description, raw_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (user_id, tx_type, amount, currency, category, description, raw_text))
            row = cur.fetchone()
        conn.commit()
    return row["id"]


def get_last_transaction(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, type, amount::float, currency, category, description,
                       to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
                FROM transactions WHERE user_id = %s ORDER BY id DESC LIMIT 1
            """, (user_id,))
            row = cur.fetchone()
    if not row:
        return None
    return (row["id"], row["type"], float(row["amount"]), row["currency"],
            row["category"], row["description"], row["created_at"])


def delete_transaction(tx_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM transactions WHERE id = %s", (tx_id,))
        conn.commit()


def get_transactions(user_id, date_from, date_to):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, type, amount::float, currency, category, description,
                       to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
                FROM transactions
                WHERE user_id = %s
                  AND created_at::date >= %s::date
                  AND created_at::date <= %s::date
                ORDER BY created_at ASC
            """, (user_id, date_from, date_to))
            rows = cur.fetchall()
    return [(r["id"], r["type"], float(r["amount"]), r["currency"],
             r["category"], r["description"], r["created_at"]) for r in rows]


def get_last_n(user_id, n=10):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, type, amount::float, currency, category, description,
                       to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
                FROM transactions WHERE user_id = %s ORDER BY id DESC LIMIT %s
            """, (user_id, n))
            rows = cur.fetchall()
    return [(r["id"], r["type"], float(r["amount"]), r["currency"],
             r["category"], r["description"], r["created_at"]) for r in rows]


# ── Категории ─────────────────────────────────────────────────────────────────

def get_user_categories(user_id, cat_type=None):
    """Возвращает пользовательские категории"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            if cat_type:
                cur.execute("""
                    SELECT name, type FROM user_categories
                    WHERE user_id = %s AND (type = %s OR type = 'both')
                    ORDER BY name
                """, (user_id, cat_type))
            else:
                cur.execute("""
                    SELECT name, type FROM user_categories
                    WHERE user_id = %s ORDER BY name
                """, (user_id,))
            rows = cur.fetchall()
    return [(r["name"], r["type"]) for r in rows]


def get_all_categories(user_id, cat_type="expense"):
    """Базовые + пользовательские категории"""
    user_cats = [name for name, t in get_user_categories(user_id, cat_type)]
    if cat_type == "expense":
        base = DEFAULT_CATEGORIES_EXPENSE
    else:
        base = DEFAULT_CATEGORIES_INCOME
    # Пользовательские сначала, потом базовые (без дублей)
    all_cats = user_cats + [c for c in base if c not in user_cats]
    return all_cats


def add_user_category(user_id, name, cat_type="expense"):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_categories (user_id, name, type)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, name) DO UPDATE SET type = EXCLUDED.type
            """, (user_id, name, cat_type))
        conn.commit()


def delete_user_category(user_id, name):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM user_categories WHERE user_id = %s AND name = %s
            """, (user_id, name))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0


# ── Бюджеты ───────────────────────────────────────────────────────────────────

def set_budget(user_id, category, amount, currency="ARS"):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO budgets (user_id, category, amount, currency)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, category)
                DO UPDATE SET amount = EXCLUDED.amount, currency = EXCLUDED.currency
            """, (user_id, category, amount, currency))
        conn.commit()


def get_budgets(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT category, amount::float, currency
                FROM budgets WHERE user_id = %s ORDER BY category
            """, (user_id,))
            rows = cur.fetchall()
    return [(r["category"], float(r["amount"]), r["currency"]) for r in rows]


def delete_budget(user_id, category):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM budgets WHERE user_id = %s AND category = %s", (user_id, category))
        conn.commit()


def get_month_spent(user_id, category, currency="ARS"):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0)::float as total
                FROM transactions
                WHERE user_id = %s AND type = 'expense'
                  AND category = %s AND currency = %s
                  AND date_trunc('month', created_at) = date_trunc('month', NOW())
            """, (user_id, category, currency))
            row = cur.fetchone()
    return float(row["total"]) if row else 0.0


# ── Настройки ─────────────────────────────────────────────────────────────────

def get_user_settings(user_id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
    return dict(row) if row else None


def set_user_settings(user_id, budgets_enabled=False, onboarded=False):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_settings (user_id, budgets_enabled, onboarded)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    budgets_enabled = COALESCE(EXCLUDED.budgets_enabled, user_settings.budgets_enabled),
                    onboarded = COALESCE(EXCLUDED.onboarded, user_settings.onboarded)
            """, (user_id, budgets_enabled, onboarded))
        conn.commit()


def update_user_setting(user_id, field, value):
    allowed = {"budgets_enabled", "onboarded"}
    if field not in allowed:
        return
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO user_settings (user_id, {field})
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET {field} = EXCLUDED.{field}
            """, (user_id, value))
        conn.commit()
