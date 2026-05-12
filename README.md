# 💰 FinBot — Telegram бот для учёта финансов

Записывай доходы и расходы голосом или текстом. Профессиональные Excel-отчёты за любой период.
База данных: **PostgreSQL**. Хостинг: **Railway** или **Render** (бесплатно).

---

## 💬 Как пользоваться

Просто пиши или говори:

| Что написать | Что запишет |
|---|---|
| `потратил 5000 на еду` | Расход 5 000 ARS · Еда |
| `кофе 800` | Расход 800 ARS |
| `получил 80000 зарплата` | Доход 80 000 ARS |
| `50 долларов такси` | Расход 50 USD |
| `заработал 200 евро фриланс` | Доход 200 EUR |

> Просто число без валюты = **всегда пессо (ARS)**

Команды: `/report`, `/report неделя`, `/report 2025-03`, `/report 01.01.2025 31.03.2025`, `/last`, `/undo`

---

## 🚀 Деплой на Railway (рекомендуется)

### 1. Залей код на GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ТВО_ИМЯ/finbot.git
git push -u origin main
```

### 2. Создай проект на Railway
1. [railway.app](https://railway.app) → Sign in with GitHub
2. **New Project** → **Deploy from GitHub repo** → выбери `finbot`
3. Railway увидит `railway.toml` и настроит автоматически

### 3. Добавь PostgreSQL
1. В проекте: **+ New** → **Database** → **Add PostgreSQL**
2. Переменная `DATABASE_URL` появится в боте **автоматически** — ничего делать не нужно!

### 4. Добавь переменные окружения
В сервисе бота → вкладка **Variables**:

| Ключ | Значение |
|---|---|
| `BOT_TOKEN` | `1234567890:AAF...` (от @BotFather) |
| `OPENAI_API_KEY` | `sk-...` (опционально — для голоса) |

> `DATABASE_URL` уже добавлен Railway автоматически — не трогай!

### 5. Готово!
Railway задеплоит автоматически. Логи → `🚀 FinBot запущен!` — пиши боту.

**Стоимость:** $5/месяц бесплатного кредита от Railway — боту хватает с запасом.

---

## 🌐 Альтернатива: Render

1. Залей на GitHub (шаг 1 выше)
2. [render.com](https://render.com) → New → **Blueprint** → подключи репозиторий
3. Render прочитает `render.yaml` и создаст Worker + PostgreSQL автоматически
4. В переменных добавь `BOT_TOKEN` и опционально `OPENAI_API_KEY`

> Render: PostgreSQL бесплатно 90 дней, потом $7/мес. Railway выгоднее.

---

## 🔑 Получить токены

**Telegram Bot Token:**
1. [@BotFather](https://t.me/BotFather) → `/newbot` → придумай имя и username
2. Скопируй токен `1234567890:AAF-xyz...`

**OpenAI API Key** (для голосовых и умного парсинга):
1. [platform.openai.com](https://platform.openai.com) → API Keys → Create
2. Без него бот работает, но не принимает голосовые

---

## 🏗 Структура
```
finbot_pg/
├── bot.py              # Точка входа
├── requirements.txt
├── Procfile
├── railway.toml
├── render.yaml
├── handlers/
│   ├── transaction.py  # Текстовые транзакции
│   ├── voice.py        # Голос → Whisper
│   └── report.py       # Отчёты + Excel
├── utils/
│   ├── db.py           # PostgreSQL
│   └── parser.py       # AI-парсинг
└── exports/
    └── excel.py        # Генератор .xlsx
```

---
*🎂 Подарок на день рождения — с любовью*
