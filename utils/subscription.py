"""Система подписки — проверка доступа, Stars, CryptoBot"""

import os
import httpx
from datetime import datetime, timedelta
from utils.db import get_conn

# ── Конфиг ────────────────────────────────────────────────────────────────────

TRIAL_DAYS = 7
SUBSCRIPTION_DAYS = 30
STARS_PRICE = 395          # ~$5
CRYPTO_PRICE_USDT = 5.0    # $5 в USDT

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")

# VIP пользователи — вписываешь Telegram ID, им всё бесплатно навсегда
VIP_USER_IDS = set(
    int(x.strip())
    for x in os.getenv("VIP_USER_IDS", "").split(",")
    if x.strip().isdigit()
)


# ── БД ────────────────────────────────────────────────────────────────────────

def init_subscription_table():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id         BIGINT PRIMARY KEY,
                    status          TEXT NOT NULL DEFAULT 'trial'
                                    CHECK(status IN ('trial','active','expired','vip')),
                    trial_started   TIMESTAMP,
                    paid_until      TIMESTAMP,
                    payment_method  TEXT,
                    total_payments  INTEGER DEFAULT 0,
                    created_at      TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payment_log (
                    id              SERIAL PRIMARY KEY,
                    user_id         BIGINT NOT NULL,
                    method          TEXT NOT NULL,
                    amount          TEXT,
                    currency        TEXT,
                    external_id     TEXT,
                    created_at      TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()


def get_subscription(user_id: int) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM subscriptions WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
    return dict(row) if row else None


def create_trial(user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO subscriptions (user_id, status, trial_started)
                VALUES (%s, 'trial', NOW())
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))
        conn.commit()


def activate_subscription(user_id: int, method: str, external_id: str = None, amount: str = None, currency: str = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            # Продлеваем от текущей даты или от paid_until если ещё активна
            cur.execute("""
                INSERT INTO subscriptions (user_id, status, paid_until, payment_method, total_payments)
                VALUES (%s, 'active', NOW() + INTERVAL '30 days', %s, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    status = 'active',
                    paid_until = GREATEST(NOW(), COALESCE(subscriptions.paid_until, NOW())) + INTERVAL '30 days',
                    payment_method = EXCLUDED.payment_method,
                    total_payments = subscriptions.total_payments + 1
            """, (user_id, method))
            if external_id:
                cur.execute("""
                    INSERT INTO payment_log (user_id, method, amount, currency, external_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, method, amount, currency, external_id))
        conn.commit()


def set_vip(user_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO subscriptions (user_id, status)
                VALUES (%s, 'vip')
                ON CONFLICT (user_id) DO UPDATE SET status = 'vip'
            """, (user_id,))
        conn.commit()


# ── Проверка доступа ──────────────────────────────────────────────────────────

def check_access(user_id: int) -> dict:
    """
    Возвращает:
      allowed: bool
      status: 'vip' | 'trial' | 'active' | 'expired'
      days_left: int (для триала и активной подписки)
      message: str (если доступ закрыт)
    """
    # VIP из переменной окружения
    if user_id in VIP_USER_IDS:
        return {"allowed": True, "status": "vip", "days_left": None}

    sub = get_subscription(user_id)

    if not sub:
        # Первый раз — создаём триал
        create_trial(user_id)
        return {"allowed": True, "status": "trial", "days_left": TRIAL_DAYS}

    if sub["status"] == "vip":
        return {"allowed": True, "status": "vip", "days_left": None}

    if sub["status"] == "active":
        paid_until = sub["paid_until"]
        if paid_until and paid_until > datetime.now():
            days_left = (paid_until - datetime.now()).days
            return {"allowed": True, "status": "active", "days_left": days_left}
        else:
            # Истекла — меняем статус
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE subscriptions SET status='expired' WHERE user_id=%s", (user_id,))
                conn.commit()
            return {"allowed": False, "status": "expired", "days_left": 0,
                    "message": "expired"}

    if sub["status"] == "trial":
        trial_started = sub["trial_started"]
        if trial_started:
            days_passed = (datetime.now() - trial_started).days
            days_left = TRIAL_DAYS - days_passed
            if days_left > 0:
                return {"allowed": True, "status": "trial", "days_left": days_left}
        # Триал истёк
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE subscriptions SET status='expired' WHERE user_id=%s", (user_id,))
            conn.commit()
        return {"allowed": False, "status": "expired", "days_left": 0,
                "message": "trial_expired"}

    # expired
    return {"allowed": False, "status": "expired", "days_left": 0,
            "message": "expired"}


# ── CryptoBot ─────────────────────────────────────────────────────────────────

async def create_crypto_invoice(user_id: int) -> dict | None:
    """Создаёт инвойс в CryptoBot, возвращает {pay_url, invoice_id}"""
    if not CRYPTOBOT_TOKEN:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://pay.crypt.bot/api/createInvoice",
                headers={"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN},
                json={
                    "asset": "USDT",
                    "amount": str(CRYPTO_PRICE_USDT),
                    "description": f"FinBot подписка 30 дней | user:{user_id}",
                    "payload": str(user_id),
                    "allow_comments": False,
                    "allow_anonymous": False,
                    "expires_in": 3600  # 1 час
                }
            )
        data = resp.json()
        if data.get("ok"):
            inv = data["result"]
            return {"pay_url": inv["pay_url"], "invoice_id": inv["invoice_id"]}
    except Exception:
        pass
    return None


async def check_crypto_payment(invoice_id: str) -> bool:
    """Проверяет оплачен ли инвойс"""
    if not CRYPTOBOT_TOKEN:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://pay.crypt.bot/api/getInvoices",
                headers={"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN},
                params={"invoice_ids": invoice_id}
            )
        data = resp.json()
        if data.get("ok"):
            items = data["result"].get("items", [])
            if items and items[0].get("status") == "paid":
                return True
    except Exception:
        pass
    return False
