"""Онбординг — выбор языка, приветствие, вопрос про бюджет"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.db import get_user_settings, set_user_settings, update_user_setting, get_user_language, set_user_language
from utils.i18n import t


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)

    # Уже онбордился — просто приветствие
    if settings and settings.get("onboarded"):
        lang = get_user_language(user_id)
        await update.message.reply_text(
            t("welcome_back", lang),
            parse_mode="Markdown"
        )
        return

    # Новый пользователь — сначала выбор языка
    keyboard = [[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]]
    await update.message.reply_text(
        "👋 Hi! / Привет! / ¡Hola!\n\n🌐 Choose your language / Выбери язык / Elige tu idioma:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Смена языка /language"""
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    keyboard = [[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
    ]]
    await update.message.reply_text(
        t("change_language", lang),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_onboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # Выбор языка
    if query.data.startswith("lang_"):
        lang = query.data[5:]  # ru / es / en
        set_user_language(user_id, lang)

        settings = get_user_settings(user_id)
        if settings and settings.get("onboarded"):
            # Просто смена языка
            await query.edit_message_text(t("language_set", lang), parse_mode="Markdown")
            return

        # Новый пользователь — показываем приветствие + вопрос про бюджет
        keyboard = [[
            InlineKeyboardButton(t("budget_question_yes", lang), callback_data="onboard_budget_yes"),
            InlineKeyboardButton(t("budget_question_no", lang), callback_data="onboard_budget_no"),
        ]]
        await query.edit_message_text(
            t("language_set", lang) + "\n\n" + t("welcome_new", lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    lang = get_user_language(user_id)

    if query.data == "onboard_budget_yes":
        set_user_settings(user_id, budgets_enabled=True, onboarded=True)
        from handlers.budget import BUDGET_CATEGORIES
        keyboard = []
        row = []
        for cat in BUDGET_CATEGORIES:
            row.append(InlineKeyboardButton(cat, callback_data=f"bset_{cat}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(
            "✅ " + ("Listo" if lang == "es" else "Done" if lang == "en" else "Готово"),
            callback_data="bset_done"
        )])

        title = {"ru": "💰 *Настройка бюджетов*\n\nНажми на категорию чтобы задать лимит.",
                 "es": "💰 *Configurar presupuestos*\n\nToca una categoría para establecer el límite.",
                 "en": "💰 *Set up budgets*\n\nTap a category to set its limit."}.get(lang, "")

        await query.edit_message_text(title, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "onboard_budget_no":
        set_user_settings(user_id, budgets_enabled=False, onboarded=True)
        msg = {"ru": "✅ *Отлично, начинаем!*\n\nПросто пиши или говори что потратил/получил.\n\nБюджеты можно включить позже: /budget set",
               "es": "✅ *¡Perfecto, empecemos!*\n\nEscribe o di lo que gastaste/recibiste.\n\nPuedes configurar presupuestos después: /budget set",
               "en": "✅ *Great, let's start!*\n\nJust write or say what you spent/received.\n\nYou can set up budgets later: /budget set"}.get(lang, "")
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif query.data == "bset_done":
        update_user_setting(user_id, "onboarded", True)
        from utils.db import get_budgets
        budgets = get_budgets(user_id)
        if budgets:
            header = {"ru": "✅ *Бюджеты настроены:*\n",
                      "es": "✅ *Presupuestos configurados:*\n",
                      "en": "✅ *Budgets set:*\n"}.get(lang, "")
            footer = {"ru": "\nВсё готово! Начинай записывать траты 🚀",
                      "es": "\n¡Todo listo! Empieza a registrar tus gastos 🚀",
                      "en": "\nAll set! Start recording your expenses 🚀"}.get(lang, "")
            lines = [header]
            for cat, amount, curr in budgets:
                lines.append(f"• {cat}: {amount:,.0f} {curr}".replace(",", "."))
            lines.append(footer)
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown")
        else:
            msg = {"ru": "✅ *Готово!* Начинай записывать 🚀\n\nДобавить бюджеты: /budget set",
                   "es": "✅ *¡Listo!* Empieza a registrar 🚀\n\nAgregar presupuestos: /budget set",
                   "en": "✅ *Done!* Start recording 🚀\n\nAdd budgets: /budget set"}.get(lang, "")
            await query.edit_message_text(msg, parse_mode="Markdown")
