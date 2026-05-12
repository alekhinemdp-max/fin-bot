"""Парсинг транзакций из натурального языка через Claude API"""

import re
import json
import os
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

CATEGORIES_EXPENSE = [
    "Еда и продукты", "Кафе и рестораны", "Транспорт", "Такси",
    "Коммунальные услуги", "Связь и интернет", "Одежда", "Здоровье и аптека",
    "Развлечения", "Образование", "Путешествия", "Дом и ремонт",
    "Техника и электроника", "Подарки", "Бизнес-расходы", "Прочее"
]

CATEGORIES_INCOME = [
    "Зарплата", "Фриланс", "Бизнес", "Аренда", "Инвестиции",
    "Подарок", "Возврат долга", "Прочее"
]

SYSTEM_PROMPT = """Ты парсер финансовых транзакций. 
Пользователь пишет на русском, испанском или английском языке.

Определи:
1. Тип: "income" (доход) или "expense" (расход)
2. Сумму (число)
3. Валюту: "ARS" по умолчанию, "USD" если упомянуты доллары/dólares/dollars/USD/$, "EUR" если евро/euros/EUR/€
4. Категорию из списка
5. Краткое описание (1-5 слов)

ВАЖНО: Если указано просто число без валюты — это ВСЕГДА ARS (пессо).
Доллары только если явно написано "долларов", "dólares", "USD", "$100" и т.д.

Расходы (expene): потратил, купил, заплатил, стоит, gaste, compré, pagué, spent, bought
Доходы (income): получил, заработал, пришло, зарплата, recibí, gané, cobré, earned, received

Отвечай ТОЛЬКО JSON, без пояснений:
{
  "type": "expense",
  "amount": 5000,
  "currency": "ARS",
  "category": "Еда и продукты",
  "description": "продукты в супермаркете"
}

Категории для расходов: """ + ", ".join(CATEGORIES_EXPENSE) + """
Категории для доходов: """ + ", ".join(CATEGORIES_INCOME)


async def parse_transaction_ai(text: str) -> dict | None:
    """Парсит транзакцию через OpenAI API"""
    if not OPENAI_API_KEY:
        return parse_transaction_regex(text)
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                }
            )
        data = resp.json()
        raw = data["choices"][0]["message"]["content"].strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        result = json.loads(raw)
        
        # Валидация
        if result.get("amount", 0) <= 0:
            return None
        if result.get("type") not in ("income", "expense"):
            return None
            
        return result
    except Exception:
        # Fallback на regex если AI недоступен
        return parse_transaction_regex(text)


def parse_transaction_regex(text: str) -> dict | None:
    """Простой regex-парсер как fallback"""
    text_lower = text.lower()
    
    # Определяем валюту
    currency = "ARS"
    if re.search(r'\b(долларов|долларес|dólares|dollars|usd)\b|\$\s*\d', text_lower):
        currency = "USD"
    elif re.search(r'\b(евро|euros|eur)\b|€', text_lower):
        currency = "EUR"
    
    # Ищем число
    amounts = re.findall(r'[\d]+(?:[.,]\d+)?', text)
    if not amounts:
        return None
    amount = float(amounts[0].replace(",", "."))
    if amount <= 0:
        return None
    
    # Тип транзакции
    income_words = r'\b(получил|заработал|пришло|зарплата|доход|recibí|gané|cobré|earned|received|ingreso)\b'
    expense_words = r'\b(потратил|купил|заплатил|стоит|расход|gaste|compré|pagué|spent|bought|gasto)\b'
    
    if re.search(income_words, text_lower):
        tx_type = "income"
        category = "Прочее"
    elif re.search(expense_words, text_lower):
        tx_type = "expense"
        category = "Прочее"
    else:
        # По умолчанию — расход
        tx_type = "expense"
        category = "Прочее"
    
    # Простая категоризация
    cats_expense = {
        "Еда и продукты": r'еда|продукт|магазин|супермаркет|comida|mercado|super',
        "Кафе и рестораны": r'кафе|ресторан|cafe|restaurant|pizza|sushi',
        "Транспорт": r'транспорт|автобус|метро|transporte|colectivo|subte',
        "Такси": r'такси|uber|cabify|taxi|remis',
        "Коммунальные услуги": r'комуналк|свет|газ|вода|luz|gas|agua|expensas',
        "Здоровье и аптека": r'аптек|врач|лекарств|farmacia|médico|salud',
        "Зарплата": r'зарплата|sueldo|salario',
    }
    
    for cat, pattern in cats_expense.items():
        if re.search(pattern, text_lower):
            category = cat
            break
    
    # Убираем числа из описания
    description = re.sub(r'[\d.,]+', '', text).strip()
    description = description[:50] if description else text[:50]
    
    return {
        "type": tx_type,
        "amount": amount,
        "currency": currency,
        "category": category,
        "description": description
    }
