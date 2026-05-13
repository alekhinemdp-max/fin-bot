#!/usr/bin/env python3
"""💰 FinBot — Telegram бот для учёта финансов"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

from handlers.onboarding import handle_start, handle_onboard_callback
from handlers.transaction import handle_text_transaction, handle_undo_callback
from handlers.voice import handle_voice_transaction
from handlers.report import handle_report_command, handle_report_text
from handlers.budget import (
    handle_budget_command, handle_budget_callback,
    handle_setbudget_command, handle_budget_amount_input
)
from utils.reset import handle_reset_ask, handle_reset_callback
from utils.db import init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Справка FinBot*\n\n"
        "*Записывать транзакции:*\n"
        "Просто пиши или говори!\n\n"
        "📥 Доходы: получил, заработал, пришло\n"
        "📤 Расходы: потратил, купил, заплатил\n\n"
        "💱 *Валюты:*\n"
        "• Просто число → пессо (ARS)\n"
        "• + долларов/USD → USD\n"
        "• + евро/EUR → EUR\n\n"
        "📊 *Отчёты:*\n"
        "`/report` — текущий месяц\n"
        "`/report неделя` — 7 дней\n"
        "`/report 2025-03` — март 2025\n"
        "`/report 01.03 31.03` — период\n\n"
        "💰 *Бюджеты:*\n"
        "`/budget` — статус всех бюджетов\n"
        "`/budget set` — настроить бюджет\n"
        "`/setbudget Еда 50000` — быстро\n\n"
        "🔧 *Прочее:*\n"
        "`/last` — последние 10 записей\n"
        "`/undo` — отменить последнюю\n"
        "`/reset` — очистить все записи",
        parse_mode="Markdown"
    )


async def handle_smart_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Роутер — бюджет, отчёт или транзакция"""
    # Если ожидаем сумму бюджета
    if context.user_data.get("awaiting_budget_amount"):
        await handle_budget_amount_input(update, context)
        return

    text = update.message.text.lower()
    report_kw = ["отчёт", "отчет", "report", "покажи", "сколько", "итого"]
    budget_kw = ["бюджет", "budget", "лимит"]

    if any(kw in text for kw in budget_kw):
        await handle_budget_command(update, context)
    elif any(kw in text for kw in report_kw):
        await handle_report_text(update, context)
    else:
        await handle_text_transaction(update, context)


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("report", handle_report_command))
    app.add_handler(CommandHandler("stats", handle_report_command))
    app.add_handler(CommandHandler("last", handle_report_command))
    app.add_handler(CommandHandler("undo", handle_report_command))
    app.add_handler(CommandHandler("reset", handle_reset_ask))
    app.add_handler(CommandHandler("budget", handle_budget_command))
    app.add_handler(CommandHandler("setbudget", handle_setbudget_command))

    # Callback кнопки
    app.add_handler(CallbackQueryHandler(handle_undo_callback, pattern="^undo_"))
    app.add_handler(CallbackQueryHandler(handle_reset_callback, pattern="^reset_"))
    app.add_handler(CallbackQueryHandler(handle_budget_callback, pattern="^bset_"))
    app.add_handler(CallbackQueryHandler(handle_onboard_callback, pattern="^onboard_"))

    # Сообщения
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_transaction))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_smart_message))

    logger.info("🚀 FinBot запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
