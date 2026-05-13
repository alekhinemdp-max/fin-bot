"""База данных PostgreSQL"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError(
            "❌ Переменная DATABASE_URL не задана!\n"
            "На Railway: добавь PostgreSQL сервис — переменная появится автоматически."
        )
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Транзакции
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
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_date
                ON transactions(user_id, created_at)
            """)
            # Бюджеты
            cur.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id          SERIAL PRIMARY KEY,
                    user_id     BIGINT NOT NULL,
                    category    TEXT NOT NULL,
                    amount      NUMERIC(15, 2) NOT NULL,
                    currency    TEXT NOT NULL DEFAULT 'ARS',
                    created_at  TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, category)
                )
            """)
            # Настройки пользователя (включён ли бюджет)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id         BIGINT PRIMARY KEY,
                    budgets_enabled BOOLEAN DEFAULT FALSE,
                    onboarded       BOOLEAN DEFAULT FALSE,
                    created_at      TIMESTAMP DEFAULT NOW()
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
    """Сколько потрачено в текущем месяце по категории"""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COALESCE(SUM(amount), 0)::float as total
                FROM transactions
                WHERE user_id = %s
                  AND type = 'expense'
                  AND category = %s
                  AND currency = %s
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


def set_user_settings(user_id, budgets_enabled=None, onboarded=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_settings (user_id, budgets_enabled, onboarded)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    budgets_enabled = COALESCE(EXCLUDED.budgets_enabled, user_settings.budgets_enabled),
                    onboarded = COALESCE(EXCLUDED.onboarded, user_settings.onboarded)
            """, (user_id,
                  budgets_enabled if budgets_enabled is not None else False,
                  onboarded if onboarded is not None else False))
        conn.commit()


def update_user_setting(user_id, field, value):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO user_settings (user_id, {field})
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET {field} = EXCLUDED.{field}
            """, (user_id, value))
        conn.commit()
