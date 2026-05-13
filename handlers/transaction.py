"""Обработка текстовых транзакций"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.parser import parse_transaction_ai
from utils.db import save_transaction, delete_transaction, get_user_settings

CURRENCY_SYMBOLS = {"ARS": "$ ARS", "USD": "💵 USD", "EUR": "💶 EUR"}
TYPE_EMOJI = {"income": "📥", "expense": "📤"}


async def handle_text_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await update.message.chat.send_action("typing")

    result = await parse_transaction_ai(text)

    if not result:
        await update.message.reply_text(
            "🤔 Не понял транзакцию. Попробуй написать чётче:\n\n"
            "• `потратил 5000 на еду`\n"
            "• `получил 80000 зарплата`\n"
            "• `кофе 800`\n"
            "• `50 долларов такси`",
            parse_mode="Markdown"
        )
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

    emoji = TYPE_EMOJI[result["type"]]
    type_text = "Доход" if result["type"] == "income" else "Расход"
    curr = CURRENCY_SYMBOLS.get(result["currency"], result["currency"])
    amount_fmt = f"{result['amount']:,.0f}".replace(",", ".")

    keyboard = [[InlineKeyboardButton("↩️ Отменить", callback_data=f"undo_{tx_id}")]]

    await update.message.reply_text(
        f"{emoji} *{type_text} записан*\n\n"
        f"💰 Сумма: *{amount_fmt} {curr}*\n"
        f"🏷 Категория: {result.get('category', 'Прочее')}\n"
        f"📝 Описание: _{result.get('description', '')}_\n\n"
        f"_#{tx_id}_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Проверка бюджета после расхода
    if result["type"] == "expense" and result["currency"] == "ARS":
        settings = get_user_settings(user_id)
        if settings and settings.get("budgets_enabled"):
            from handlers.budget import check_budget_after_expense
            warning = await check_budget_after_expense(user_id, result.get("category", "Прочее"), None)
            if warning:
                await update.message.reply_text(warning, parse_mode="Markdown")


async def handle_undo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("undo_"):
        tx_id = int(query.data.split("_")[1])
        delete_transaction(tx_id)
        await query.edit_message_text(f"✅ Запись #{tx_id} удалена.", parse_mode="Markdown")
