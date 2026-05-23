"""Декоратор проверки доступа — оборачивает любой хендлер"""

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from utils.subscription import check_access
from handlers.payment import show_paywall


def require_access(func):
    """
    Декоратор — проверяет подписку перед выполнением хендлера.
    Использование:
        @require_access
        async def handle_something(update, context): ...
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None
        if not user_id:
            return

        access = check_access(user_id)

        if access["allowed"]:
            # Напоминание если мало времени осталось
            if access["status"] == "trial" and access["days_left"] <= 2:
                msg = update.message or (update.callback_query.message if update.callback_query else None)
                if msg:
                    await msg.reply_text(
                        f"⚠️ Пробный период заканчивается через *{access['days_left']} дн.*\n"
                        f"Оформи подписку чтобы не потерять доступ: /subscribe",
                        parse_mode="Markdown"
                    )
            elif access["status"] == "active" and access["days_left"] <= 3:
                msg = update.message or (update.callback_query.message if update.callback_query else None)
                if msg:
                    await msg.reply_text(
                        f"⚠️ Подписка заканчивается через *{access['days_left']} дн.*\n"
                        f"Продли: /subscribe",
                        parse_mode="Markdown"
                    )
            return await func(update, context, *args, **kwargs)
        else:
            await show_paywall(update, status=access.get("message", "expired"))

    return wrapper
