"""Обработка голосовых сообщений через OpenAI Whisper"""

import os
import tempfile
import httpx
from telegram import Update
from telegram.ext import ContextTypes

from handlers.transaction import handle_text_transaction

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def handle_voice_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Голосовое → текст (Whisper) → транзакция"""
    
    await update.message.chat.send_action("typing")
    
    voice = update.message.voice or update.message.audio
    if not voice:
        await update.message.reply_text("❌ Не удалось получить аудио файл.")
        return
    
    if not OPENAI_API_KEY:
        await update.message.reply_text(
            "⚠️ Голосовые сообщения требуют OpenAI API ключ.\n"
            "Добавь `OPENAI_API_KEY` в переменные окружения.\n\n"
            "Пока напиши текстом 📝",
            parse_mode="Markdown"
        )
        return
    
    try:
        file = await context.bot.get_file(voice.file_id)
        
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
        
        await file.download_to_drive(tmp_path)
        
        # Транскрипция через Whisper
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
            await update.message.reply_text("🤔 Не удалось распознать речь. Попробуй ещё раз.")
            return
        
        # Показываем что распознали
        await update.message.reply_text(f"🎙 Распознал: _{transcript}_", parse_mode="Markdown")
        
        # Обрабатываем как текст
        update.message.text = transcript
        await handle_text_transaction(update, context)
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при обработке голосового: {str(e)[:100]}\n\nПопробуй написать текстом."
        )
