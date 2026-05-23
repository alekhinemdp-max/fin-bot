"""Парсинг транзакций — одиночных и списком"""

import re
import json
import os
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

DEFAULT_CATEGORIES_EXPENSE = [
    "Еда и продукты", "Кафе и рестораны", "Транспорт", "Такси",
    "Коммунальные услуги", "Связь и интернет", "Одежда",
    "Здоровье и аптека", "Развлечения", "Образование",
    "Путешествия", "Дом и ремонт", "Техника", "Подарки",
    "Бизнес-расходы", "Аренда", "Прочее"
]

DEFAULT_CATEGORIES_INCOME = [
    "Зарплата", "Фриланс", "Бизнес", "Аренда",
    "Инвестиции", "Подарок", "Возврат долга", "Прочее"
]


def build_system_prompt(extra_expense_cats=None, extra_income_cats=None):
    exp_cats = (extra_expense_cats or []) + DEFAULT_CATEGORIES_EXPENSE
    inc_cats = (extra_income_cats or []) + DEFAULT_CATEGORIES_INCOME

    return f"""Ты парсер финансовых транзакций. Пользователь пишет на русском, испанском или английском.

Твоя задача — найти ВСЕ транзакции в тексте и вернуть их списком.

Для каждой транзакции определи:
1. type: "income" или "expense"
2. amount: число
3. currency: "ARS" по умолчанию, "USD" если долларов/dólares/USD/$, "EUR" если евро/EUR/€
4. category: из списка ниже
5. description: 1-5 слов описания

ВАЖНО:
- Просто число без валюты = ВСЕГДА ARS
- Если в тексте несколько строк или перечисление — это несколько транзакций, верни все
- Если тип не указан явно — считай расходом (expense)

Отвечай ТОЛЬКО JSON массивом без пояснений:
[
  {{"type": "expense", "amount": 1000, "currency": "ARS", "category": "Кафе и рестораны", "description": "cafe"}},
  {{"type": "expense", "amount": 2300, "currency": "ARS", "category": "Такси", "description": "taxi"}}
]

Категории расходов: {", ".join(exp_cats)}
Категории доходов: {", ".join(inc_cats)}"""


async def parse_transactions_ai(text: str, user_id: int = None) -> list[dict]:
    """
    Парсит ОДНУ ИЛИ НЕСКОЛЬКО транзакций из текста.
    Всегда возвращает список.
    """
    extra_expense = []
    extra_income = []
    if user_id:
        try:
            from utils.db import get_user_categories
            user_cats = get_user_categories(user_id)
            for name, cat_type in user_cats:
                if cat_type in ("expense", "both"):
                    extra_expense.append(name)
                if cat_type in ("income", "both"):
                    extra_income.append(name)
        except Exception:
            pass

    if not OPENAI_API_KEY:
        return parse_transactions_regex(text, extra_expense + extra_income)

    try:
        system_prompt = build_system_prompt(extra_expense, extra_income)
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800
                }
            )
        data = resp.json()
        raw = data["choices"][0]["message"]["content"].strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        results = json.loads(raw)

        if isinstance(results, dict):
            results = [results]

        valid = []
        for r in results:
            if r.get("amount", 0) > 0 and r.get("type") in ("income", "expense"):
                valid.append(r)
        return valid

    except Exception:
        return parse_transactions_regex(text, extra_expense + extra_income)


# Обратная совместимость — старый код вызывает parse_transaction_ai (единственное число)
async def parse_transaction_ai(text: str, user_id: int = None) -> dict | None:
    results = await parse_transactions_ai(text, user_id)
    return results[0] if results else None


def parse_transactions_regex(text: str, extra_categories=None) -> list[dict]:
    """Regex-парсер — обрабатывает каждую строку отдельно"""
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]

    # Если одна строка — пробуем найти несколько транзакций в ней
    if len(lines) == 1:
        lines = re.split(r'[,;]', lines[0])
        lines = [l.strip() for l in lines if l.strip()]

    results = []
    for line in lines:
        r = _parse_single_regex(line, extra_categories)
        if r:
            results.append(r)
    return results


def _parse_single_regex(text: str, extra_categories=None) -> dict | None:
    text_lower = text.lower().strip()
    if not text_lower:
        return None

    # Валюта
    currency = "ARS"
    if re.search(r'\b(долларов|долларес|dólares|dollars|usd)\b|\$\s*\d', text_lower):
        currency = "USD"
    elif re.search(r'\b(евро|euros|eur)\b|€', text_lower):
        currency = "EUR"

    # Сумма
    amounts = re.findall(r'[\d]+(?:[.,]\d+)?', text)
    if not amounts:
        return None
    amount = float(amounts[0].replace(",", "."))
    if amount <= 0:
        return None

    # Тип
    income_kw = r'\b(получил|заработал|пришло|зарплата|доход|recibí|gané|cobré|earned|received|ingreso|salario|sueldo)\b'
    tx_type = "income" if re.search(income_kw, text_lower) else "expense"

    # Категория — сначала личные
    category = "Прочее"
    if extra_categories:
        for cat in extra_categories:
            if cat.lower() in text_lower:
                category = cat
                break

    if category == "Прочее":
        cat_patterns = {
            "Кафе и рестораны": r'кафе|ресторан|cafe|restaurant|coffee|кофе',
            "Еда и продукты": r'еда|продукт|магазин|супермаркет|comida|mercado|super|almuerzo|cena',
            "Транспорт": r'транспорт|автобус|метро|colectivo|subte|tren',
            "Такси": r'такси|uber|cabify|taxi|remis',
            "Аренда": r'аренд|alquiler|rent',
            "Коммунальные услуги": r'комуналк|свет|газ|вода|luz|gas|agua|expensas',
            "Здоровье и аптека": r'аптек|врач|лекарств|farmacia|médico|salud',
            "Зарплата": r'зарплата|sueldo|salario',
            "Фриланс": r'фриланс|freelance',
            "Развлечения": r'кино|театр|cinema|entretenimiento',
            "Одежда": r'одежд|ropa|clothes',
        }
        for cat, pattern in cat_patterns.items():
            if re.search(pattern, text_lower):
                category = cat
                break

    # Описание — убираем числа, оставляем слова
    description = re.sub(r'[\d.,]+', '', text).strip()
    description = description[:40] if description else text[:40]

    return {
        "type": tx_type,
        "amount": amount,
        "currency": currency,
        "category": category,
        "description": description.strip()
    }
