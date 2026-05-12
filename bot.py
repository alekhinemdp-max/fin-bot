#!/usr/bin/env python3
"""
💰 FinBot — Telegram бот для учёта доходов и расходов
Автор подарка: с любовью ❤️
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

from handlers.transaction import handle_text_transaction
from handlers.voice import handle_voice_transaction
from handlers.report import handle_report_command, handle_report_text
from utils.reset import handle_reset_ask, handle_reset_callback
from handlers.transaction import handle_undo_callback
from utils.db import init_db

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_KEY_HERE")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Привет! Я твой финансовый помощник.*\n\n"
        "Просто напиши или скажи что потратил/получил:\n\n"
        "💬 *Примеры:*\n"
        "• `потратил 5000 на еду`\n"
        "• `получил 50000 зарплата`\n"
        "• `кофе 800`\n"
        "• `100 долларов такси`\n"
        "• `заработал 200 евро фриланс`\n\n"
        "📊 *Отчёты:*\n"
        "• `/report` — за текущий месяц\n"
        "• `/report неделя` — за 7 дней\n"
        "• `/report 2025-01` — за январь 2025\n"
        "• `/report 01.01.2025 31.01.2025` — произвольный период\n\n"
        "🎙 *Голосовые сообщения тоже работают!*\n\n"
        "💡 По умолчанию всё в *пессо*. "
        "Доллары/евро указывай явно: `100 долларов` или `50 USD`",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Справка FinBot*\n\n"
        "*Как записывать транзакции:*\n"
        "Просто пиши естественным языком!\n\n"
        "📥 *Доходы:* получил, заработал, пришло, доход, зарплата\n"
        "📤 *Расходы:* потратил, купил, заплатил, расход, стоит\n\n"
        "💱 *Валюты:*\n"
        "• Просто число → пессо (ARS)\n"
        "• + `долларов/долларес/USD/$` → USD\n"
        "• + `евро/EUR/€` → EUR\n\n"
        "📊 *Команды:*\n"
        "`/report` — месяц\n"
        "`/report неделя` — 7 дней\n"
        "`/report сегодня` — сегодня\n"
        "`/report 2025-03` — март 2025\n"
        "`/report 01.03.2025 31.03.2025` — период\n"
        "`/stats` — общая статистика\n"
        "`/last` — последние 10 записей\n"
        "`/undo` — отменить последнюю запись\n",
        parse_mode="Markdown"
    )


def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("report", handle_report_command))
    app.add_handler(CommandHandler("stats", handle_report_command))
    app.add_handler(CommandHandler("last", handle_report_command))
    app.add_handler(CommandHandler("undo", handle_report_command))
    app.add_handler(CommandHandler("reset", handle_reset_ask))
    
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(handle_undo_callback, pattern="^undo_"))
    app.add_handler(CallbackQueryHandler(handle_reset_callback, pattern="^reset_"))
    
    app.add_handler(MessageHandler(
        filters.VOICE | filters.AUDIO,
        handle_voice_transaction
    ))
    
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_smart_message
    ))
    
    logger.info("🚀 FinBot запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def handle_smart_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Роутер — отчёт или транзакция"""
    text = update.message.text.lower()
    report_keywords = ["отчёт", "отчет", "report", "покажи", "сколько", "итого", "/report"]
    
    if any(kw in text for kw in report_keywords):
        await handle_report_text(update, context)
    else:
        await handle_text_transaction(update, context)


if __name__ == "__main__":
    main()
