"""Управление бюджетами — /budget, /setbudget, онбординг"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.db import (
    get_budgets, set_budget, delete_budget,
    get_month_spent, get_user_settings, update_user_setting
)

BUDGET_CATEGORIES = [
    "Еда и продукты", "Кафе и рестораны", "Транспорт", "Такси",
    "Коммунальные услуги", "Связь и интернет", "Одежда",
    "Здоровье и аптека", "Развлечения", "Прочее"
]

def fmt(amount):
    return f"{amount:,.0f}".replace(",", ".")

def progress_bar(pct):
    filled = int(pct / 10)
    filled = min(filled, 10)
    bar = "█" * filled + "░" * (10 - filled)
    return bar


async def handle_budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /budget          — показать статус всех бюджетов
    /budget set      — начать настройку бюджета
    /budget del Еда  — удалить бюджет категории
    """
    user_id = update.effective_user.id
    args = context.args or []

    if args and args[0].lower() in ("set", "add", "настроить"):
        await show_budget_setup(update, context)
        return

    if args and args[0].lower() in ("del", "delete", "удалить") and len(args) > 1:
        category = " ".join(args[1:])
        delete_budget(user_id, category)
        await update.message.reply_text(f"✅ Бюджет для *{category}* удалён.", parse_mode="Markdown")
        return

    await show_budget_status(update, user_id)


async def show_budget_status(update: Update, user_id: int):
    """Показывает статус всех бюджетов текущего месяца"""
    budgets = get_budgets(user_id)

    if not budgets:
        await update.message.reply_text(
            "📋 Бюджеты не настроены.\n\n"
            "Чтобы добавить: /budget set\n"
            "Или напиши `/setbudget Еда 50000`",
            parse_mode="Markdown"
        )
        return

    from datetime import datetime
    month = datetime.now().strftime("%B %Y")
    lines = [f"📊 *Бюджеты на {month}*\n"]

    for category, limit, currency in budgets:
        spent = get_month_spent(user_id, category, currency)
        pct = (spent / limit * 100) if limit > 0 else 0
        bar = progress_bar(pct)
        remaining = limit - spent

        if pct >= 100:
            status = "🔴"
        elif pct >= 80:
            status = "🟡"
        else:
            status = "🟢"

        lines.append(
            f"{status} *{category}*\n"
            f"  `{bar}` {pct:.0f}%\n"
            f"  Потрачено: {fmt(spent)} / {fmt(limit)} {currency}\n"
            f"  {'⚠️ Превышен на ' + fmt(abs(remaining)) if remaining < 0 else 'Остаток: ' + fmt(remaining)} {currency}\n"
        )

    lines.append("_/budget set — добавить бюджет_")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def show_budget_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Интерактивная настройка — выбор категории"""
    keyboard = []
    row = []
    for i, cat in enumerate(BUDGET_CATEGORIES):
        row.append(InlineKeyboardButton(cat, callback_data=f"bset_{cat}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="bset_cancel")])

    await update.message.reply_text(
        "💰 *Настройка бюджета*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_budget_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка inline-кнопок при настройке бюджета"""
    query = update.callback_query
    await query.answer()

    if query.data == "bset_cancel":
        await query.edit_message_text("❌ Настройка отменена.")
        return

    if query.data.startswith("bset_"):
        category = query.data[5:]
        context.user_data["budget_category"] = category
        await query.edit_message_text(
            f"💰 *{category}*\n\nНапиши сумму лимита в пессо (ARS):\n\n"
            f"Например: `50000`",
            parse_mode="Markdown"
        )
        context.user_data["awaiting_budget_amount"] = True


async def handle_budget_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Принимает сумму бюджета от пользователя"""
    user_id = update.effective_user.id
    text = update.message.text.strip().replace(".", "").replace(",", "")

    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Укажи число, например: `50000`", parse_mode="Markdown")
        return

    category = context.user_data.get("budget_category", "Прочее")
    set_budget(user_id, category, amount, "ARS")
    context.user_data.pop("awaiting_budget_amount", None)
    context.user_data.pop("budget_category", None)

    await update.message.reply_text(
        f"✅ Бюджет установлен!\n\n"
        f"🏷 *{category}*: {fmt(amount)} ARS / месяц\n\n"
        f"Добавить ещё? /budget set\n"
        f"Статус всех бюджетов: /budget",
        parse_mode="Markdown"
    )


async def handle_setbudget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /setbudget Еда 50000
    Быстрая установка без кнопок
    """
    user_id = update.effective_user.id
    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "Использование: `/setbudget Категория Сумма`\n\n"
            "Например:\n"
            "`/setbudget Еда и продукты 50000`\n"
            "`/setbudget Такси 15000`",
            parse_mode="Markdown"
        )
        return

    try:
        amount = float(args[-1].replace(".", "").replace(",", ""))
        category = " ".join(args[:-1])
    except ValueError:
        await update.message.reply_text("❌ Последний аргумент должен быть числом.", parse_mode="Markdown")
        return

    set_budget(user_id, category, amount, "ARS")
    await update.message.reply_text(
        f"✅ *{category}*: {fmt(amount)} ARS / месяц",
        parse_mode="Markdown"
    )


async def check_budget_after_expense(user_id: int, category: str, bot) -> str | None:
    """
    Вызывается после записи расхода.
    Возвращает предупреждение если >= 80%, None если всё ок.
    """
    budgets = get_budgets(user_id)
    budget_map = {cat: (limit, curr) for cat, limit, curr in budgets}

    if category not in budget_map:
        return None

    limit, currency = budget_map[category]
    spent = get_month_spent(user_id, category, currency)
    pct = (spent / limit * 100) if limit > 0 else 0

    if pct >= 100:
        return (
            f"🔴 *Бюджет превышен!*\n"
            f"Категория *{category}*: потрачено {fmt(spent)} из {fmt(limit)} ARS "
            f"({pct:.0f}%)\n"
            f"Превышение: {fmt(spent - limit)} ARS"
        )
    elif pct >= 80:
        return (
            f"🟡 *Внимание!* Бюджет на *{category}* использован на {pct:.0f}%\n"
            f"Потрачено {fmt(spent)} из {fmt(limit)} ARS — "
            f"остаток {fmt(limit - spent)} ARS"
        )
    return None
