"""Обработка голосовых сообщений"""

import os, tempfile
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.parser import parse_transaction_ai
from utils.db import save_transaction, get_user_language
from utils.i18n import t

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CURRENCY_SYMBOLS = {"ARS": "$ ARS", "USD": "💵 USD", "EUR": "💶 EUR"}
TYPE_EMOJI = {"income": "📥", "expense": "📤"}


async def handle_voice_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_language(user_id)
    await update.message.chat.send_action("typing")

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    if not OPENAI_API_KEY:
        await update.message.reply_text(t("voice_no_openai", lang))
        return

    try:
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        await file.download_to_drive(tmp_path)

        async with httpx.AsyncClient(timeout=30) as client:
            with open(tmp_path, "rb") as audio_file:
                resp = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    files={"file": ("audio.ogg", audio_file, "audio/ogg")},
                    data={"model": "whisper-1"}
                )
        os.unlink(tmp_path)

        if resp.status_code != 200:
            raise Exception(f"Whisper error: {resp.text}")

        transcript = resp.json().get("text", "").strip()
        if not transcript:
            await update.message.reply_text(t("voice_not_recognized", lang))
            return

        await update.message.reply_text(f"{t('voice_recognized', lang)}: _{transcript}_", parse_mode="Markdown")

        result = await parse_transaction_ai(transcript, user_id=user_id)
        if not result:
            await update.message.reply_text(t("not_understood", lang), parse_mode="Markdown")
            return

        tx_id = save_transaction(
            user_id=user_id,
            tx_type=result["type"],
            amount=result["amount"],
            currency=result["currency"],
            category=result.get("category", "Прочее"),
            description=result.get("description", transcript[:100]),
            raw_text=transcript
        )

        type_key = "income_recorded" if result["type"] == "income" else "expense_recorded"
        curr = CURRENCY_SYMBOLS.get(result["currency"], result["currency"])
        amount_fmt = f"{result['amount']:,.0f}".replace(",", ".")
        keyboard = [[InlineKeyboardButton(t("undo_button", lang), callback_data=f"undo_{tx_id}")]]

        await update.message.reply_text(
            f"{t(type_key, lang)}\n\n"
            f"{t('amount_label', lang)}: *{amount_fmt} {curr}*\n"
            f"{t('category_label', lang)}: {result.get('category', 'Прочее')}\n"
            f"{t('description_label', lang)}: _{result.get('description', '')}_\n\n"
            f"_#{tx_id}_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await update.message.reply_text(t("voice_error", lang))
