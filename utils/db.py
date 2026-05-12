"""База данных PostgreSQL — для Railway/Render деплоя"""

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
        conn.commit()


def save_transaction(user_id, tx_type, amount, currency, category, description, raw_text):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transactions (user_id, type, amount, currency, category, description, raw_text)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
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
