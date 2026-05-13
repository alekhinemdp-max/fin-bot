"""Онбординг нового пользователя — /start с вопросом про бюджет"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.db import get_user_settings, set_user_settings, update_user_setting


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name or "друг"
    settings = get_user_settings(user_id)

    # Уже онбордился — просто приветствие
    if settings and settings.get("onboarded"):
        budgets_status = "включены ✅" if settings.get("budgets_enabled") else "выключены"
        await update.message.reply_text(
            f"👋 *Привет, {first_name}!*\n\n"
            f"Я помню тебя 😊 Бюджеты: {budgets_status}\n\n"
            f"Просто пиши или говори что потратил/получил.\n"
            f"Команды: /help — справка · /budget — бюджеты · /report — отчёт",
            parse_mode="Markdown"
        )
        return

    # Новый пользователь — онбординг
    keyboard = [[
        InlineKeyboardButton("✅ Да, настроить бюджеты", callback_data="onboard_budget_yes"),
        InlineKeyboardButton("➡️ Пропустить", callback_data="onboard_budget_no"),
    ]]

    await update.message.reply_text(
        f"👋 *Привет, {first_name}! Я твой финансовый помощник.*\n\n"
        f"Записываю доходы и расходы голосом или текстом, "
        f"веду учёт по категориям и присылаю Excel-отчёты.\n\n"
        f"💬 *Как пользоваться:*\n"
        f"• `потратил 5000 на еду`\n"
        f"• `получил 80000 зарплата`\n"
        f"• `50 долларов такси`\n"
        f"• 🎙 Голосовые тоже работают!\n\n"
        f"💡 По умолчанию всё в пессо (ARS). "
        f"Доллары/евро указывай явно.\n\n"
        f"─────────────────\n"
        f"*Хочешь настроить месячные бюджеты по категориям?*\n"
        f"Буду напоминать когда трата приближается к лимиту.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_onboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

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
        keyboard.append([InlineKeyboardButton("✅ Готово, начать работу", callback_data="bset_done")])

        await query.edit_message_text(
            "💰 *Настройка бюджетов*\n\n"
            "Нажми на категорию чтобы задать лимит.\n"
            "Можно настроить несколько. Когда закончишь — нажми «Готово».",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "onboard_budget_no":
        set_user_settings(user_id, budgets_enabled=False, onboarded=True)
        await query.edit_message_text(
            "✅ *Отлично, начинаем!*\n\n"
            "Просто пиши или говори что потратил/получил.\n\n"
            "Бюджеты можно включить позже командой /budget set",
            parse_mode="Markdown"
        )

    elif query.data == "bset_done":
        update_user_setting(user_id, "onboarded", True)
        from utils.db import get_budgets
        budgets = get_budgets(user_id)
        if budgets:
            lines = ["✅ *Бюджеты настроены:*\n"]
            for cat, amount, curr in budgets:
                lines.append(f"• {cat}: {amount:,.0f} {curr}".replace(",", "."))
            lines.append("\nВсё готово! Начинай записывать траты 🚀")
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown")
        else:
            await query.edit_message_text(
                "✅ *Готово!* Начинай записывать траты 🚀\n\n"
                "Добавить бюджеты позже: /budget set",
                parse_mode="Markdown"
            )
