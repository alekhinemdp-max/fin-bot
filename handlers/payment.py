"""Обработка платежей — Stars и CryptoBot"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from utils.subscription import (
    STARS_PRICE, CRYPTO_PRICE_USDT,
    activate_subscription, create_crypto_invoice, check_crypto_payment,
    check_access
)


def get_paywall_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⭐ Оплатить {STARS_PRICE} Stars", callback_data="pay_stars")],
        [InlineKeyboardButton(f"💵 Оплатить {CRYPTO_PRICE_USDT} USDT (крипто)", callback_data="pay_crypto")],
        [InlineKeyboardButton("✅ Я уже оплатил крипто", callback_data="pay_crypto_check")],
    ])


async def show_paywall(update: Update, status: str = "expired"):
    """Показывает сообщение с предложением оплатить"""
    if status == "trial_expired":
        header = (
            "⏰ *Пробный период закончился*\n\n"
            "Надеюсь, бот был полезен! 😊\n\n"
        )
    else:
        header = (
            "🔒 *Подписка истекла*\n\n"
            "Продли чтобы продолжить вести учёт.\n\n"
        )

    text = (
        header +
        "💎 *FinBot Premium — 30 дней*\n\n"
        "✅ Учёт доходов и расходов\n"
        "✅ Голосовые сообщения\n"
        "✅ Excel-отчёты за любой период\n"
        "✅ Бюджеты по категориям\n"
        "✅ Личные категории\n\n"
        f"💰 Цена: *{STARS_PRICE} Stars* или *{CRYPTO_PRICE_USDT} USDT*"
    )

    if hasattr(update, "message") and update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_paywall_keyboard())
    elif hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_paywall_keyboard())


async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if query.data == "pay_stars":
        await query.edit_message_text(
            f"⭐ *Оплата через Telegram Stars*\n\n"
            f"Нажми кнопку ниже — откроется стандартное окно оплаты Telegram.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"⭐ Оплатить {STARS_PRICE} Stars", callback_data="pay_stars_invoice")],
                [InlineKeyboardButton("◀️ Назад", callback_data="pay_back")]
            ])
        )

    elif query.data == "pay_stars_invoice":
        # Отправляем инвойс Stars
        await context.bot.send_invoice(
            chat_id=user_id,
            title="FinBot Premium",
            description="Подписка на 30 дней — учёт финансов, отчёты, бюджеты",
            payload=f"sub_{user_id}",
            currency="XTR",           # XTR = Telegram Stars
            prices=[LabeledPrice("FinBot Premium 30 дней", STARS_PRICE)],
        )
        await query.answer("Инвойс отправлен! ⬆️")

    elif query.data == "pay_crypto":
        await query.edit_message_text("⏳ Создаю инвойс...", parse_mode="Markdown")
        invoice = await create_crypto_invoice(user_id)

        if not invoice:
            await query.edit_message_text(
                "❌ Крипто-оплата временно недоступна. Попробуй Stars.",
                reply_markup=get_paywall_keyboard()
            )
            return

        # Сохраняем invoice_id в контексте
        context.user_data["crypto_invoice_id"] = invoice["invoice_id"]

        await query.edit_message_text(
            f"💵 *Оплата через CryptoBot*\n\n"
            f"Сумма: *{CRYPTO_PRICE_USDT} USDT*\n\n"
            f"1. Нажми кнопку «Оплатить» ниже\n"
            f"2. Переведи USDT в CryptoBot\n"
            f"3. Вернись и нажми «Я оплатил»\n\n"
            f"⏰ Инвойс действует 1 час",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💵 Открыть CryptoBot", url=invoice["pay_url"])],
                [InlineKeyboardButton("✅ Я оплатил", callback_data="pay_crypto_check")],
                [InlineKeyboardButton("◀️ Назад", callback_data="pay_back")],
            ])
        )

    elif query.data == "pay_crypto_check":
        invoice_id = context.user_data.get("crypto_invoice_id")
        if not invoice_id:
            await query.answer("❌ Сначала создай инвойс — нажми «Оплатить USDT»", show_alert=True)
            return

        await query.answer("Проверяю оплату...")
        paid = await check_crypto_payment(str(invoice_id))

        if paid:
            activate_subscription(user_id, "cryptobot",
                                  external_id=str(invoice_id),
                                  amount=str(CRYPTO_PRICE_USDT),
                                  currency="USDT")
            context.user_data.pop("crypto_invoice_id", None)
            await query.edit_message_text(
                "🎉 *Оплата подтверждена!*\n\n"
                "Подписка активна на 30 дней. Продолжай вести учёт!\n\n"
                "Просто напиши или скажи что потратил/получил.",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "⏳ *Оплата ещё не поступила*\n\n"
                "Подожди 1-2 минуты и проверь снова.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Проверить снова", callback_data="pay_crypto_check")],
                    [InlineKeyboardButton("◀️ Назад", callback_data="pay_back")],
                ])
            )

    elif query.data == "pay_back":
        await show_paywall(update)


async def handle_stars_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вызывается когда Telegram подтверждает оплату Stars (pre_checkout)"""
    await update.pre_checkout_query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вызывается после успешной оплаты Stars"""
    user_id = update.effective_user.id
    payment = update.message.successful_payment
    stars = payment.total_amount

    activate_subscription(
        user_id, "stars",
        external_id=payment.telegram_payment_charge_id,
        amount=str(stars),
        currency="XTR"
    )

    await update.message.reply_text(
        f"🎉 *Спасибо! Оплата {stars} Stars получена.*\n\n"
        f"Подписка активна на *30 дней*.\n\n"
        f"Продолжай записывать доходы и расходы!",
        parse_mode="Markdown"
    )
