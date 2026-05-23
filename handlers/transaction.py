"""Обработка текстовых транзакций — одиночных и списком"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.parser import parse_transactions_ai
from utils.db import save_transaction, delete_transaction, get_user_settings, get_user_language
from utils.i18n import t

CURRENCY_SYMBOLS = {"ARS": "$ ARS", "USD": "💵 USD", "EUR": "💶 EUR"}
TYPE_EMOJI = {"income": "📥", "expense": "📤"}


def fmt(amount):
    return f"{amount:,.0f}".replace(",", ".")


async def handle_text_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    text = update.message.text
    await update.message.chat.send_action("typing")

    results = await parse_transactions_ai(text, user_id=user_id)

    if not results:
        await update.message.reply_text(t("not_understood", lang), parse_mode="Markdown")
        return

    # Одна транзакция — красивое сообщение с кнопкой отмены
    if len(results) == 1:
        r = results[0]
        tx_id = save_transaction(
            user_id=user_id, tx_type=r["type"], amount=r["amount"],
            currency=r["currency"], category=r.get("category", "Прочее"),
            description=r.get("description", text[:100]), raw_text=text
        )
        type_key = "income_recorded" if r["type"] == "income" else "expense_recorded"
        curr = CURRENCY_SYMBOLS.get(r["currency"], r["currency"])
        keyboard = [[InlineKeyboardButton(t("undo_button", lang), callback_data=f"undo_{tx_id}")]]
        await update.message.reply_text(
            f"{t(type_key, lang)}\n\n"
            f"{t('amount_label', lang)}: *{fmt(r['amount'])} {curr}*\n"
            f"{t('category_label', lang)}: {r.get('category', 'Прочее')}\n"
            f"{t('description_label', lang)}: _{r.get('description', '')}_\n\n"
            f"_#{tx_id}_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await _check_budget(update, user_id, r, lang)

    # Несколько транзакций — сводка одним сообщением
    else:
        lines = {
            "ru": [f"✅ *Записано {len(results)} транзакции:*\n"],
            "es": [f"✅ *Se registraron {len(results)} transacciones:*\n"],
            "en": [f"✅ *Recorded {len(results)} transactions:*\n"],
        }.get(lang, [f"✅ *{len(results)} transactions recorded:*\n"])

        total_expense_ars = 0
        saved_ids = []

        for r in results:
            tx_id = save_transaction(
                user_id=user_id, tx_type=r["type"], amount=r["amount"],
                currency=r["currency"], category=r.get("category", "Прочее"),
                description=r.get("description", ""), raw_text=text
            )
            saved_ids.append(tx_id)
            emoji = TYPE_EMOJI[r["type"]]
            curr = CURRENCY_SYMBOLS.get(r["currency"], r["currency"])
            lines.append(f"{emoji} *{fmt(r['amount'])} {curr}* — {r.get('category','?')} _{r.get('description','')}_")
            if r["type"] == "expense" and r["currency"] == "ARS":
                total_expense_ars += r["amount"]

        if total_expense_ars > 0:
            total_label = {"ru": "💸 Итого расходов", "es": "💸 Total gastos", "en": "💸 Total expenses"}.get(lang, "💸 Total")
            lines.append(f"\n{total_label}: *{fmt(total_expense_ars)} $ ARS*")

        # Кнопка отмены всех
        undo_label = {"ru": "↩️ Отменить все", "es": "↩️ Cancelar todo", "en": "↩️ Undo all"}.get(lang, "↩️ Undo all")
        ids_str = ",".join(str(i) for i in saved_ids)
        keyboard = [[InlineKeyboardButton(undo_label, callback_data=f"undo_multi_{ids_str}")]]

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Проверяем бюджет для каждого расхода
        for r in results:
            await _check_budget(update, user_id, r, lang)


async def _check_budget(update, user_id, r, lang):
    if r["type"] == "expense" and r["currency"] == "ARS":
        settings = get_user_settings(user_id)
        if settings and settings.get("budgets_enabled"):
            from handlers.budget import check_budget_after_expense
            warning = await check_budget_after_expense(user_id, r.get("category", "Прочее"), None, lang)
            if warning:
                await update.message.reply_text(warning, parse_mode="Markdown")


async def handle_undo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    lang = get_user_language(user_id)

    if query.data.startswith("undo_multi_"):
        ids = query.data.replace("undo_multi_", "").split(",")
        for tx_id in ids:
            delete_transaction(int(tx_id))
        n = len(ids)
        msg = {"ru": f"✅ Отменено {n} записей.", "es": f"✅ {n} registros cancelados.", "en": f"✅ {n} records cancelled."}.get(lang, f"✅ {n} cancelled.")
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif query.data.startswith("undo_"):
        tx_id = int(query.data.split("_")[1])
        delete_transaction(tx_id)
        await query.edit_message_text(t("transaction_cancelled", lang), parse_mode="Markdown")
