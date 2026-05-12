"""Команда /reset — очистка всех записей пользователя"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.db import get_conn


async def handle_reset_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Спрашивает подтверждение перед удалением"""
    keyboard = [
        [
            InlineKeyboardButton("🗑 Да, удалить всё", callback_data="reset_confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="reset_cancel"),
        ]
    ]
    await update.message.reply_text(
        "⚠️ *Удалить все твои записи?*\n\n"
        "Это действие нельзя отменить — все доходы и расходы будут удалены навсегда.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки подтверждения"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "reset_confirm":
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM transactions WHERE user_id = %s", (user_id,))
                count = cur.fetchone()["count"]
                cur.execute("DELETE FROM transactions WHERE user_id = %s", (user_id,))
            conn.commit()
        await query.edit_message_text(
            f"✅ Готово! Удалено *{count}* записей.\n\nМожешь начинать заново 🙂",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("❌ Отменено. Записи сохранены.")
