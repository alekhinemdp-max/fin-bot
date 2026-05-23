#!/usr/bin/env python3
"""💰 FinBot — Telegram бот для учёта финансов"""

import logging, os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler, PreCheckoutQueryHandler
)

from handlers.onboarding import handle_start, handle_onboard_callback, handle_language_command
from handlers.transaction import handle_text_transaction, handle_undo_callback
from handlers.voice import handle_voice_transaction
from handlers.report import handle_report_command, handle_report_text
from handlers.budget import (handle_budget_command, handle_budget_callback,
                              handle_setbudget_command, handle_budget_amount_input)
from handlers.categories import (handle_categories_command, handle_addcat_command,
                                  handle_delcat_command, handle_delcat_callback)
from handlers.payment import (handle_payment_callback, handle_stars_payment,
                               handle_successful_payment, show_paywall)
from handlers.admin import handle_admin_command
from utils.reset import handle_reset_ask, handle_reset_callback
from utils.db import init_db, get_user_language
from utils.subscription import init_subscription_table, check_access
from utils.access import require_access
from utils.i18n import t

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    texts = {
        "ru": (
            "📖 *Справка FinBot*\n\n"
            "Пиши или говори что потратил/получил!\n\n"
            "📊 `/report` — месяц · `/report неделя`\n"
            "💰 `/budget` — бюджеты · `/budget set`\n"
            "🏷 `/categories` · `/addcat Спорт` · `/delcat`\n"
            "💳 `/subscribe` — подписка · `/status`\n"
            "🌐 `/language` — сменить язык\n"
            "🔧 `/last` · `/undo` · `/reset`"
        ),
        "es": (
            "📖 *Ayuda FinBot*\n\n"
            "¡Escribe o di lo que gastaste/recibiste!\n\n"
            "📊 `/report` — mes · `/report semana`\n"
            "💰 `/budget` — presupuestos · `/budget set`\n"
            "🏷 `/categories` · `/addcat Deporte` · `/delcat`\n"
            "💳 `/subscribe` — suscripción · `/status`\n"
            "🌐 `/language` — cambiar idioma\n"
            "🔧 `/last` · `/undo` · `/reset`"
        ),
        "en": (
            "📖 *FinBot Help*\n\n"
            "Just write or say what you spent/received!\n\n"
            "📊 `/report` — month · `/report week`\n"
            "💰 `/budget` — budgets · `/budget set`\n"
            "🏷 `/categories` · `/addcat Sport` · `/delcat`\n"
            "💳 `/subscribe` — subscription · `/status`\n"
            "🌐 `/language` — change language\n"
            "🔧 `/last` · `/undo` · `/reset`"
        ),
    }
    await update.message.reply_text(texts.get(lang, texts["ru"]), parse_mode="Markdown")


async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    access = check_access(user_id)
    lang = get_user_language(user_id)
    if access["status"] == "vip":
        await update.message.reply_text(t("status_vip", lang))
        return
    await show_paywall(update, status="expired")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    access = check_access(user_id)
    days = access.get("days_left", 0)

    status_map = {
        "vip": t("status_vip", lang),
        "trial": t("status_trial", lang, days=days),
        "active": t("status_active", lang, days=days),
        "expired": t("status_expired", lang),
    }
    text = f"📋 *{status_map.get(access['status'], '?')}*"
    await update.message.reply_text(text, parse_mode="Markdown")


@require_access
async def protected_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_budget_amount"):
        await handle_budget_amount_input(update, context)
        return
    text = update.message.text.lower()
    if any(k in text for k in ["отчёт","отчет","report","покажи","reporte","semana","week"]):
        await handle_report_text(update, context)
    elif any(k in text for k in ["бюджет","budget","лимит","presupuesto"]):
        await handle_budget_command(update, context)
    else:
        await handle_text_transaction(update, context)


@require_access
async def protected_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_voice_transaction(update, context)


@require_access
async def protected_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_report_command(update, context)


@require_access
async def protected_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_budget_command(update, context)


@require_access
async def protected_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_categories_command(update, context)


@require_access
async def protected_addcat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_addcat_command(update, context)


@require_access
async def protected_delcat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_delcat_command(update, context)


def main():
    init_db()
    init_subscription_table()
    try:
        from utils.db import init_language_table
        init_language_table()
    except Exception:
        pass

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("language", handle_language_command))
    app.add_handler(CommandHandler("subscribe", subscribe_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("admin", handle_admin_command))
    app.add_handler(CommandHandler("report", protected_report))
    app.add_handler(CommandHandler("stats", protected_report))
    app.add_handler(CommandHandler("last", protected_report))
    app.add_handler(CommandHandler("undo", protected_report))
    app.add_handler(CommandHandler("reset", handle_reset_ask))
    app.add_handler(CommandHandler("budget", protected_budget))
    app.add_handler(CommandHandler("setbudget", handle_setbudget_command))
    app.add_handler(CommandHandler("categories", protected_categories))
    app.add_handler(CommandHandler("addcat", protected_addcat))
    app.add_handler(CommandHandler("delcat", protected_delcat))

    app.add_handler(PreCheckoutQueryHandler(handle_stars_payment))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))

    app.add_handler(CallbackQueryHandler(handle_undo_callback, pattern="^undo_"))
    app.add_handler(CallbackQueryHandler(handle_reset_callback, pattern="^reset_"))
    app.add_handler(CallbackQueryHandler(handle_budget_callback, pattern="^bset_"))
    app.add_handler(CallbackQueryHandler(handle_onboard_callback, pattern="^(onboard_|lang_|bset_)"))
    app.add_handler(CallbackQueryHandler(handle_delcat_callback, pattern="^delcat_"))
    app.add_handler(CallbackQueryHandler(handle_payment_callback, pattern="^pay_"))

    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, protected_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, protected_text))

    logger.info("🚀 FinBot запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
