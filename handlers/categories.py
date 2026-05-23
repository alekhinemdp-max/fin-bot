"""Управление пользовательскими категориями"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.db import (
    get_user_categories, get_all_categories,
    add_user_category, delete_user_category,
    DEFAULT_CATEGORIES_EXPENSE, DEFAULT_CATEGORIES_INCOME
)


async def handle_categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /categories        — показать все категории
    /categories income — категории доходов
    """
    user_id = update.effective_user.id
    args = context.args or []
    cat_type = "income" if args and args[0].lower() in ("income", "доходы") else "expense"

    user_cats = get_user_categories(user_id, cat_type)
    user_names = [name for name, _ in user_cats]

    if cat_type == "expense":
        base = DEFAULT_CATEGORIES_EXPENSE
        title = "📤 *Категории расходов*"
    else:
        base = DEFAULT_CATEGORIES_INCOME
        title = "📥 *Категории доходов*"

    lines = [title + "\n"]

    if user_names:
        lines.append("⭐ *Твои категории:*")
        for name in user_names:
            lines.append(f"  • {name}")
        lines.append("")

    lines.append("📋 *Стандартные:*")
    for cat in base:
        lines.append(f"  • {cat}")

    lines.append(
        "\n_Добавить: /addcat Название_\n"
        "_Удалить: /delcat Название_\n"
        "_Категории доходов: /categories income_"
    )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def handle_addcat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /addcat Спорт         — расход
    /addcat Дивиденды income — доход
    """
    user_id = update.effective_user.id
    args = context.args or []

    if not args:
        await update.message.reply_text(
            "Использование:\n"
            "`/addcat Название` — категория расходов\n"
            "`/addcat Название income` — категория доходов",
            parse_mode="Markdown"
        )
        return

    # Определяем тип
    if args[-1].lower() in ("income", "доход", "доходы"):
        cat_type = "income"
        name = " ".join(args[:-1]).strip()
    elif args[-1].lower() in ("expense", "расход", "расходы"):
        cat_type = "expense"
        name = " ".join(args[:-1]).strip()
    else:
        cat_type = "expense"
        name = " ".join(args).strip()

    if not name:
        await update.message.reply_text("❌ Укажи название категории.", parse_mode="Markdown")
        return

    if len(name) > 40:
        await update.message.reply_text("❌ Название слишком длинное (макс. 40 символов).", parse_mode="Markdown")
        return

    # Проверяем что не дубль базовой
    all_base = DEFAULT_CATEGORIES_EXPENSE + DEFAULT_CATEGORIES_INCOME
    if name in all_base:
        await update.message.reply_text(
            f"ℹ️ Категория *{name}* уже есть в стандартных.",
            parse_mode="Markdown"
        )
        return

    add_user_category(user_id, name, cat_type)
    type_label = "расходов" if cat_type == "expense" else "доходов"

    await update.message.reply_text(
        f"✅ Категория *{name}* добавлена в *{type_label}*!\n\n"
        f"Теперь бот будет её распознавать автоматически.\n"
        f"Все категории: /categories",
        parse_mode="Markdown"
    )


async def handle_delcat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/delcat Название"""
    user_id = update.effective_user.id
    args = context.args or []

    if not args:
        # Показываем кнопки для удаления
        user_cats = get_user_categories(user_id)
        if not user_cats:
            await update.message.reply_text(
                "У тебя нет своих категорий для удаления.\n"
                "Добавить: /addcat Название",
                parse_mode="Markdown"
            )
            return

        keyboard = []
        for name, _ in user_cats:
            keyboard.append([InlineKeyboardButton(f"🗑 {name}", callback_data=f"delcat_{name}")])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="delcat_cancel")])

        await update.message.reply_text(
            "Выбери категорию для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    name = " ".join(args).strip()
    deleted = delete_user_category(user_id, name)

    if deleted:
        await update.message.reply_text(
            f"✅ Категория *{name}* удалена.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"❌ Категория *{name}* не найдена в твоих категориях.\n"
            f"Стандартные категории удалить нельзя.\n\n"
            f"Твои категории: /categories",
            parse_mode="Markdown"
        )


async def handle_delcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "delcat_cancel":
        await query.edit_message_text("❌ Отменено.")
        return

    name = query.data[7:]  # убираем "delcat_"
    deleted = delete_user_category(user_id, name)

    if deleted:
        await query.edit_message_text(f"✅ Категория *{name}* удалена.", parse_mode="Markdown")
    else:
        await query.edit_message_text(f"❌ Не удалось удалить *{name}*.", parse_mode="Markdown")
