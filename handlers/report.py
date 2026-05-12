"""Отчёты и экспорт в Excel"""

import io
import re
from datetime import datetime, timedelta, date

from telegram import Update
from telegram.ext import ContextTypes

from utils.db import get_transactions, get_last_n, get_last_transaction, delete_transaction
from exports.excel import generate_excel_report


def parse_period(args_text: str):
    """
    Парсит период из текста.
    Возвращает (date_from_str, date_to_str, label)
    """
    today = date.today()
    text = args_text.strip().lower()
    
    if not text or text in ("месяц", "month", "mes"):
        first = today.replace(day=1)
        return str(first), str(today), f"{today.strftime('%B %Y')}"
    
    if text in ("неделя", "week", "semana", "7 дней"):
        week_ago = today - timedelta(days=7)
        return str(week_ago), str(today), "Последние 7 дней"
    
    if text in ("сегодня", "today", "hoy"):
        return str(today), str(today), f"Сегодня {today.strftime('%d.%m.%Y')}"
    
    if text in ("вчера", "yesterday", "ayer"):
        yesterday = today - timedelta(days=1)
        return str(yesterday), str(yesterday), f"Вчера {yesterday.strftime('%d.%m.%Y')}"
    
    if text in ("год", "year", "año"):
        first = today.replace(month=1, day=1)
        return str(first), str(today), f"Год {today.year}"
    
    # YYYY-MM формат (2025-03)
    m = re.match(r'^(\d{4})-(\d{2})$', text)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        first = date(y, mo, 1)
        if mo == 12:
            last = date(y + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(y, mo + 1, 1) - timedelta(days=1)
        return str(first), str(last), first.strftime("%B %Y")
    
    # DD.MM.YYYY DD.MM.YYYY
    m = re.match(r'(\d{2})[.\-/](\d{2})[.\-/](\d{4})\s+(\d{2})[.\-/](\d{2})[.\-/](\d{4})', text)
    if m:
        d1 = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        d2 = date(int(m.group(6)), int(m.group(5)), int(m.group(4)))
        return str(d1), str(d2), f"{d1.strftime('%d.%m.%Y')} – {d2.strftime('%d.%m.%Y')}"
    
    # По умолчанию — текущий месяц
    first = today.replace(day=1)
    return str(first), str(today), f"{today.strftime('%B %Y')}"


def format_amount(amount: float, currency: str) -> str:
    symbols = {"ARS": "$", "USD": "US$", "EUR": "€"}
    sym = symbols.get(currency, currency)
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"{sym} {formatted}"


async def handle_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка /report, /stats, /last, /undo"""
    command = update.message.text.split()[0].replace("/", "").lower()
    args = " ".join(update.message.text.split()[1:])
    user_id = update.effective_user.id
    
    if command == "undo":
        row = get_last_transaction(user_id)
        if not row:
            await update.message.reply_text("Нет записей для отмены.")
            return
        tx_id, tx_type, amount, currency, category, desc, created_at = row
        delete_transaction(tx_id)
        await update.message.reply_text(
            f"✅ Отменена последняя запись:\n"
            f"_{('Доход' if tx_type == 'income' else 'Расход')} "
            f"{format_amount(amount, currency)} — {desc}_",
            parse_mode="Markdown"
        )
        return
    
    if command == "last":
        rows = get_last_n(user_id, 10)
        if not rows:
            await update.message.reply_text("📭 Записей пока нет.")
            return
        lines = ["📋 *Последние 10 записей:*\n"]
        for row in rows:
            tx_id, tx_type, amount, currency, category, desc, created_at = row
            emoji = "📥" if tx_type == "income" else "📤"
            dt = created_at[:16] if created_at else ""
            lines.append(f"{emoji} `{dt}` {format_amount(amount, currency)} — _{desc}_ [{category}]")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return
    
    # report / stats
    date_from, date_to, label = parse_period(args)
    await send_report(update, user_id, date_from, date_to, label)


async def handle_report_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отчёт по тексту (без команды)"""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Убираем слова-триггеры
    clean = re.sub(r'отчёт|отчет|report|покажи|сколько|итого', '', text.lower()).strip()
    date_from, date_to, label = parse_period(clean)
    await send_report(update, user_id, date_from, date_to, label)


async def send_report(update: Update, user_id: int, date_from: str, date_to: str, label: str):
    rows = get_transactions(user_id, date_from, date_to)
    
    if not rows:
        await update.message.reply_text(
            f"📭 Нет записей за *{label}*",
            parse_mode="Markdown"
        )
        return
    
    # Считаем суммы по валютам
    income_by_curr = {}
    expense_by_curr = {}
    cats_expense = {}
    cats_income = {}
    
    for row in rows:
        tx_id, tx_type, amount, currency, category, desc, created_at = row
        if tx_type == "income":
            income_by_curr[currency] = income_by_curr.get(currency, 0) + amount
            cats_income[category] = cats_income.get(category, 0) + amount
        else:
            expense_by_curr[currency] = expense_by_curr.get(currency, 0) + amount
            cats_expense[category] = cats_expense.get(category, 0) + amount
    
    lines = [f"📊 *Отчёт за {label}*\n"]
    lines.append(f"📝 Всего записей: {len(rows)}\n")
    
    # Доходы
    if income_by_curr:
        lines.append("📥 *Доходы:*")
        for curr, total in sorted(income_by_curr.items()):
            lines.append(f"  {format_amount(total, curr)}")
        if cats_income:
            top = sorted(cats_income.items(), key=lambda x: x[1], reverse=True)[:3]
            lines.append("  _топ категории: " + ", ".join(f"{c}" for c, _ in top) + "_")
    
    # Расходы
    if expense_by_curr:
        lines.append("\n📤 *Расходы:*")
        for curr, total in sorted(expense_by_curr.items()):
            lines.append(f"  {format_amount(total, curr)}")
        if cats_expense:
            top = sorted(cats_expense.items(), key=lambda x: x[1], reverse=True)[:3]
            lines.append("  _топ категории: " + ", ".join(f"{c}" for c, _ in top) + "_")
    
    # Баланс (только ARS)
    if "ARS" in income_by_curr or "ARS" in expense_by_curr:
        inc_ars = income_by_curr.get("ARS", 0)
        exp_ars = expense_by_curr.get("ARS", 0)
        balance = inc_ars - exp_ars
        sign = "+" if balance >= 0 else ""
        lines.append(f"\n💼 *Баланс ARS:* `{sign}{format_amount(abs(balance), 'ARS')}`")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    
    # Генерируем и отправляем Excel
    await update.message.chat.send_action("upload_document")
    
    excel_bytes = generate_excel_report(rows, label, date_from, date_to)
    filename = f"finbot_{date_from}_{date_to}.xlsx"
    
    await update.message.reply_document(
        document=io.BytesIO(excel_bytes),
        filename=filename,
        caption=f"📎 Excel-отчёт за {label}"
    )
