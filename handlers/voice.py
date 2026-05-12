"""Обработка голосовых сообщений через OpenAI Whisper"""

import os
import tempfile
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.parser import parse_transaction_ai
from utils.db import save_transaction

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CURRENCY_SYMBOLS = {"ARS": "$ ARS", "USD": "💵 USD", "EUR": "💶 EUR"}
TYPE_EMOJI = {"income": "📥", "expense": "📤"}


async def handle_voice_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")

    voice = update.message.voice or update.message.audio
    if not voice:
        await update.message.reply_text("❌ Не удалось получить аудио.")
        return

    if not OPENAI_API_KEY:
        await update.message.reply_text(
            "⚠️ Голосовые требуют OpenAI API ключ.\n"
            "Добавь `OPENAI_API_KEY` в Variables на Railway.",
            parse_mode="Markdown"
        )
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
                    data={"model": "whisper-1", "language": "ru"}
                )
        os.unlink(tmp_path)

        if resp.status_code != 200:
            raise Exception(f"Whisper error: {resp.text}")

        transcript = resp.json().get("text", "").strip()
        if not transcript:
            await update.message.reply_text("🤔 Не удалось распознать речь.")
            return

        await update.message.reply_text(f"🎙 Распознал: _{transcript}_", parse_mode="Markdown")

        result = await parse_transaction_ai(transcript)
        if not result:
            await update.message.reply_text("🤔 Не понял транзакцию. Попробуй написать текстом.")
            return

        user_id = update.effective_user.id
        tx_id = save_transaction(
            user_id=user_id,
            tx_type=result["type"],
            amount=result["amount"],
            currency=result["currency"],
            category=result.get("category", "Прочее"),
            description=result.get("description", transcript[:100]),
            raw_text=transcript
        )

        emoji = TYPE_EMOJI[result["type"]]
        type_text = "Доход" if result["type"] == "income" else "Расход"
        curr = CURRENCY_SYMBOLS.get(result["currency"], result["currency"])
        amount_fmt = f"{result['amount']:,.0f}".replace(",", ".")
        keyboard = [[InlineKeyboardButton("↩️ Отменить", callback_data=f"undo_{tx_id}")]]

        await update.message.reply_text(
            f"{emoji} *{type_text} записан*\n\n"
            f"💰 Сумма: *{amount_fmt} {curr}*\n"
            f"🏷 Категория: {result.get('category', 'Прочее')}\n"
            f"📝 Описание: _{result.get('description', '')}_\n\n"
            f"_#{tx_id}_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:150]}\n\nПопробуй написать текстом.")
