"""Обработка текстовых транзакций"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.parser import parse_transaction_ai
from utils.db import save_transaction, delete_transaction, get_user_settings, get_user_language
from utils.i18n import t

CURRENCY_SYMBOLS = {"ARS": "$ ARS", "USD": "💵 USD", "EUR": "💶 EUR"}
TYPE_EMOJI = {"income": "📥", "expense": "📤"}


async def handle_text_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    text = update.message.text
    await update.message.chat.send_action("typing")

    result = await parse_transaction_ai(text, user_id=user_id)

    if not result:
        await update.message.reply_text(t("not_understood", lang), parse_mode="Markdown")
        return

    tx_id = save_transaction(
        user_id=user_id,
        tx_type=result["type"],
        amount=result["amount"],
        currency=result["currency"],
        category=result.get("category", "Прочее"),
        description=result.get("description", text[:100]),
        raw_text=text
    )

    type_key = "income_recorded" if result["type"] == "income" else "expense_recorded"
    curr = CURRENCY_SYMBOLS.get(result["currency"], result["currency"])
    amount_fmt = f"{result['amount']:,.0f}".replace(",", ".")
    keyboard = [[InlineKeyboardButton(t("undo_button", lang), callback_data=f"undo_{tx_id}")]]

    await update.message.reply_text(
        f"{t(type_key, lang)}\n\n"
        f"{t('amount_label', lang)}: *{amount_fmt} {curr}*\n"
        f"{t('category_label', lang)}: {result.get('category', 'Прочее')}\n"
        f"{t('description_label', lang)}: _{result.get('description', '')}_\n\n"
        f"_#{tx_id}_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Проверка бюджета
    if result["type"] == "expense" and result["currency"] == "ARS":
        settings = get_user_settings(user_id)
        if settings and settings.get("budgets_enabled"):
            from handlers.budget import check_budget_after_expense
            warning = await check_budget_after_expense(user_id, result.get("category", "Прочее"), None, lang)
            if warning:
                await update.message.reply_text(warning, parse_mode="Markdown")


async def handle_undo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    if query.data.startswith("undo_"):
        tx_id = int(query.data.split("_")[1])
        delete_transaction(tx_id)
        await query.edit_message_text(t("transaction_cancelled", lang), parse_mode="Markdown")
