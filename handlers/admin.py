"""Админ-команды — только для владельца бота"""

import os
from telegram import Update
from telegram.ext import ContextTypes
from utils.subscription import set_vip, get_subscription, activate_subscription, VIP_USER_IDS
from utils.db import get_conn

OWNER_ID = int(os.getenv("OWNER_ID", "0"))


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /admin vip 123456789       — дать VIP пользователю
    /admin grant 123456789     — активировать подписку на 30 дней
    /admin info 123456789      — инфо о пользователе
    /admin stats               — статистика по всем пользователям
    """
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return  # Молча игнорируем

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "🔧 *Админ-панель*\n\n"
            "`/admin vip ID` — дать VIP\n"
            "`/admin grant ID` — дать 30 дней\n"
            "`/admin info ID` — инфо о юзере\n"
            "`/admin stats` — статистика",
            parse_mode="Markdown"
        )
        return

    cmd = args[0].lower()

    if cmd == "stats":
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, COUNT(*) as cnt
                    FROM subscriptions GROUP BY status
                """)
                rows = cur.fetchall()
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM transactions")
                active_users = cur.fetchone()["count"]
                cur.execute("SELECT COUNT(*) FROM payment_log")
                payments = cur.fetchone()["count"]

        lines = ["📊 *Статистика бота*\n"]
        for row in rows:
            emoji = {"vip": "👑", "active": "✅", "trial": "🆓", "expired": "❌"}.get(row["status"], "•")
            lines.append(f"{emoji} {row['status']}: *{row['cnt']}*")
        lines.append(f"\n👤 Активных (с транзакциями): *{active_users}*")
        lines.append(f"💳 Всего платежей: *{payments}*")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    if len(args) < 2:
        await update.message.reply_text("Укажи ID пользователя.")
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Неверный ID.")
        return

    if cmd == "vip":
        set_vip(target_id)
        await update.message.reply_text(f"👑 Пользователь `{target_id}` получил VIP.", parse_mode="Markdown")

    elif cmd == "grant":
        activate_subscription(target_id, "admin_grant")
        await update.message.reply_text(f"✅ Пользователю `{target_id}` выдана подписка на 30 дней.", parse_mode="Markdown")

    elif cmd == "info":
        sub = get_subscription(target_id)
        if not sub:
            await update.message.reply_text(f"Пользователь `{target_id}` не найден.", parse_mode="Markdown")
            return
        await update.message.reply_text(
            f"👤 *Пользователь {target_id}*\n\n"
            f"Статус: `{sub['status']}`\n"
            f"Триал начат: {sub.get('trial_started', '—')}\n"
            f"Оплачено до: {sub.get('paid_until', '—')}\n"
            f"Способ оплаты: {sub.get('payment_method', '—')}\n"
            f"Всего платежей: {sub.get('total_payments', 0)}",
            parse_mode="Markdown"
        )
