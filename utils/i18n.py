"""Интернационализация — все тексты бота на трёх языках"""

TEXTS = {

    # ── Онбординг ─────────────────────────────────────────────────────────────
    "choose_language": {
        "ru": "👋 Привет! На каком языке будем общаться?",
        "es": "👋 ¡Hola! ¿En qué idioma quieres que hablemos?",
        "en": "👋 Hi! What language would you like to use?",
    },
    "language_set": {
        "ru": "🇷🇺 Отлично, говорим по-русски!",
        "es": "🇪🇸 ¡Perfecto, hablamos en español!",
        "en": "🇬🇧 Great, we'll speak English!",
    },
    "welcome_new": {
        "ru": (
            "*Я твой финансовый помощник.*\n\n"
            "Записываю доходы и расходы голосом или текстом, "
            "веду учёт по категориям и присылаю Excel-отчёты.\n\n"
            "💬 *Примеры:*\n"
            "• `потратил 5000 на еду`\n"
            "• `получил 80000 зарплата`\n"
            "• `50 долларов такси`\n"
            "• 🎙 Голосовые тоже работают!\n\n"
            "💡 По умолчанию всё в пессо (ARS).\n\n"
            "─────────────────\n"
            "*Хочешь настроить месячные бюджеты?*"
        ),
        "es": (
            "*Soy tu asistente financiero.*\n\n"
            "Registro ingresos y gastos por voz o texto, "
            "llevo el control por categorías y envío reportes en Excel.\n\n"
            "💬 *Ejemplos:*\n"
            "• `gasté 5000 en comida`\n"
            "• `recibí 80000 sueldo`\n"
            "• `50 dólares taxi`\n"
            "• 🎙 ¡Los mensajes de voz también funcionan!\n\n"
            "💡 Por defecto todo en pesos (ARS).\n\n"
            "─────────────────\n"
            "*¿Quieres configurar presupuestos mensuales?*"
        ),
        "en": (
            "*I'm your financial assistant.*\n\n"
            "I record income and expenses by voice or text, "
            "track by category and send Excel reports.\n\n"
            "💬 *Examples:*\n"
            "• `spent 5000 on food`\n"
            "• `received 80000 salary`\n"
            "• `50 dollars taxi`\n"
            "• 🎙 Voice messages work too!\n\n"
            "💡 Default currency is pesos (ARS).\n\n"
            "─────────────────\n"
            "*Would you like to set up monthly budgets?*"
        ),
    },
    "welcome_back": {
        "ru": "👋 *Привет!* Просто пиши или говори что потратил/получил.\n`/help` — справка · `/budget` — бюджеты · `/report` — отчёт",
        "es": "👋 *¡Hola!* Solo escribe o di lo que gastaste/recibiste.\n`/help` — ayuda · `/budget` — presupuestos · `/report` — reporte",
        "en": "👋 *Welcome back!* Just write or say what you spent/received.\n`/help` — help · `/budget` — budgets · `/report` — report",
    },
    "budget_question_yes": {
        "ru": "✅ Да, настроить бюджеты",
        "es": "✅ Sí, configurar presupuestos",
        "en": "✅ Yes, set up budgets",
    },
    "budget_question_no": {
        "ru": "➡️ Пропустить",
        "es": "➡️ Omitir",
        "en": "➡️ Skip",
    },

    # ── Транзакции ────────────────────────────────────────────────────────────
    "income_recorded": {
        "ru": "📥 *Доход записан*",
        "es": "📥 *Ingreso registrado*",
        "en": "📥 *Income recorded*",
    },
    "expense_recorded": {
        "ru": "📤 *Расход записан*",
        "es": "📤 *Gasto registrado*",
        "en": "📤 *Expense recorded*",
    },
    "amount_label": {
        "ru": "💰 Сумма",
        "es": "💰 Monto",
        "en": "💰 Amount",
    },
    "category_label": {
        "ru": "🏷 Категория",
        "es": "🏷 Categoría",
        "en": "🏷 Category",
    },
    "description_label": {
        "ru": "📝 Описание",
        "es": "📝 Descripción",
        "en": "📝 Description",
    },
    "undo_button": {
        "ru": "↩️ Отменить",
        "es": "↩️ Cancelar",
        "en": "↩️ Undo",
    },
    "not_understood": {
        "ru": (
            "🤔 Не понял транзакцию. Попробуй:\n\n"
            "• `потратил 5000 на еду`\n"
            "• `получил 80000 зарплата`\n"
            "• `50 долларов такси`"
        ),
        "es": (
            "🤔 No entendí la transacción. Intenta:\n\n"
            "• `gasté 5000 en comida`\n"
            "• `recibí 80000 sueldo`\n"
            "• `50 dólares taxi`"
        ),
        "en": (
            "🤔 Didn't understand. Try:\n\n"
            "• `spent 5000 on food`\n"
            "• `received 80000 salary`\n"
            "• `50 dollars taxi`"
        ),
    },
    "transaction_cancelled": {
        "ru": "✅ Запись отменена.",
        "es": "✅ Registro cancelado.",
        "en": "✅ Record cancelled.",
    },

    # ── Голос ─────────────────────────────────────────────────────────────────
    "voice_recognized": {
        "ru": "🎙 Распознал",
        "es": "🎙 Reconocí",
        "en": "🎙 Recognized",
    },
    "voice_no_openai": {
        "ru": "⚠️ Голосовые требуют OpenAI API ключ.",
        "es": "⚠️ Los mensajes de voz requieren una clave OpenAI API.",
        "en": "⚠️ Voice messages require an OpenAI API key.",
    },
    "voice_not_recognized": {
        "ru": "🤔 Не удалось распознать речь.",
        "es": "🤔 No se pudo reconocer el audio.",
        "en": "🤔 Couldn't recognize the audio.",
    },
    "voice_error": {
        "ru": "❌ Ошибка при обработке голосового. Попробуй написать текстом.",
        "es": "❌ Error al procesar el audio. Intenta escribir.",
        "en": "❌ Error processing voice. Try writing instead.",
    },

    # ── Отчёты ────────────────────────────────────────────────────────────────
    "report_empty": {
        "ru": "📭 Нет записей за этот период.",
        "es": "📭 No hay registros para este período.",
        "en": "📭 No records for this period.",
    },
    "report_title": {
        "ru": "📊 *Отчёт за*",
        "es": "📊 *Reporte de*",
        "en": "📊 *Report for*",
    },
    "report_records": {
        "ru": "📝 Всего записей",
        "es": "📝 Total registros",
        "en": "📝 Total records",
    },
    "income_label": {
        "ru": "📥 *Доходы:*",
        "es": "📥 *Ingresos:*",
        "en": "📥 *Income:*",
    },
    "expense_label": {
        "ru": "📤 *Расходы:*",
        "es": "📤 *Gastos:*",
        "en": "📤 *Expenses:*",
    },
    "balance_label": {
        "ru": "💼 *Баланс ARS:*",
        "es": "💼 *Balance ARS:*",
        "en": "💼 *Balance ARS:*",
    },
    "excel_caption": {
        "ru": "📎 Excel-отчёт за",
        "es": "📎 Reporte Excel de",
        "en": "📎 Excel report for",
    },
    "top_categories": {
        "ru": "топ категории",
        "es": "top categorías",
        "en": "top categories",
    },

    # ── Бюджеты ───────────────────────────────────────────────────────────────
    "budget_title": {
        "ru": "📊 *Бюджеты на*",
        "es": "📊 *Presupuestos de*",
        "en": "📊 *Budgets for*",
    },
    "budget_empty": {
        "ru": "📋 Бюджеты не настроены.\n\nДобавить: /budget set",
        "es": "📋 No hay presupuestos configurados.\n\nAgregar: /budget set",
        "en": "📋 No budgets configured.\n\nAdd: /budget set",
    },
    "budget_exceeded": {
        "ru": "🔴 *Бюджет превышен!*\nКатегория *{cat}*: потрачено {spent} из {limit} ARS ({pct:.0f}%)\nПревышение: {over} ARS",
        "es": "🔴 *¡Presupuesto superado!*\nCategoría *{cat}*: gastado {spent} de {limit} ARS ({pct:.0f}%)\nExceso: {over} ARS",
        "en": "🔴 *Budget exceeded!*\nCategory *{cat}*: spent {spent} of {limit} ARS ({pct:.0f}%)\nOver by: {over} ARS",
    },
    "budget_warning": {
        "ru": "🟡 *Внимание!* Бюджет на *{cat}* использован на {pct:.0f}%\nПотрачено {spent} из {limit} ARS — остаток {left} ARS",
        "es": "🟡 *¡Atención!* Presupuesto de *{cat}* usado al {pct:.0f}%\nGastado {spent} de {limit} ARS — quedan {left} ARS",
        "en": "🟡 *Warning!* Budget for *{cat}* is {pct:.0f}% used\nSpent {spent} of {limit} ARS — {left} ARS remaining",
    },
    "budget_set_ok": {
        "ru": "✅ Бюджет установлен!\n\n🏷 *{cat}*: {amount} ARS / месяц",
        "es": "✅ ¡Presupuesto configurado!\n\n🏷 *{cat}*: {amount} ARS / mes",
        "en": "✅ Budget set!\n\n🏷 *{cat}*: {amount} ARS / month",
    },

    # ── Подписка ──────────────────────────────────────────────────────────────
    "status_vip": {
        "ru": "👑 VIP — бесплатно навсегда",
        "es": "👑 VIP — gratis para siempre",
        "en": "👑 VIP — free forever",
    },
    "status_trial": {
        "ru": "🆓 Пробный период — осталось {days} дн.",
        "es": "🆓 Período de prueba — quedan {days} días",
        "en": "🆓 Trial period — {days} days left",
    },
    "status_active": {
        "ru": "✅ Подписка активна — осталось {days} дн.",
        "es": "✅ Suscripción activa — quedan {days} días",
        "en": "✅ Subscription active — {days} days left",
    },
    "status_expired": {
        "ru": "❌ Подписка истекла",
        "es": "❌ Suscripción vencida",
        "en": "❌ Subscription expired",
    },
    "trial_ending": {
        "ru": "⚠️ Пробный период заканчивается через *{days} дн.*\nОформи подписку: /subscribe",
        "es": "⚠️ El período de prueba termina en *{days} días*\nSuscríbete: /subscribe",
        "en": "⚠️ Trial ends in *{days} days*\nSubscribe: /subscribe",
    },
    "sub_ending": {
        "ru": "⚠️ Подписка заканчивается через *{days} дн.*\nПродли: /subscribe",
        "es": "⚠️ La suscripción termina en *{days} días*\nRenueva: /subscribe",
        "en": "⚠️ Subscription ends in *{days} days*\nRenew: /subscribe",
    },
    "paywall_trial_expired": {
        "ru": "⏰ *Пробный период закончился*\n\nНадеюсь, бот был полезен! 😊\n\n",
        "es": "⏰ *El período de prueba terminó*\n\n¡Espero que el bot haya sido útil! 😊\n\n",
        "en": "⏰ *Trial period ended*\n\nHope the bot was useful! 😊\n\n",
    },
    "paywall_expired": {
        "ru": "🔒 *Подписка истекла*\n\nПродли чтобы продолжить.\n\n",
        "es": "🔒 *Suscripción vencida*\n\nRenueva para continuar.\n\n",
        "en": "🔒 *Subscription expired*\n\nRenew to continue.\n\n",
    },
    "paywall_features": {
        "ru": "💎 *FinBot Premium — 30 дней*\n\n✅ Учёт доходов и расходов\n✅ Голосовые сообщения\n✅ Excel-отчёты\n✅ Бюджеты\n✅ Личные категории\n\n",
        "es": "💎 *FinBot Premium — 30 días*\n\n✅ Control de ingresos y gastos\n✅ Mensajes de voz\n✅ Reportes Excel\n✅ Presupuestos\n✅ Categorías personales\n\n",
        "en": "💎 *FinBot Premium — 30 days*\n\n✅ Income & expense tracking\n✅ Voice messages\n✅ Excel reports\n✅ Budgets\n✅ Custom categories\n\n",
    },
    "pay_stars_btn": {
        "ru": "⭐ Оплатить {n} Stars",
        "es": "⭐ Pagar {n} Stars",
        "en": "⭐ Pay {n} Stars",
    },
    "pay_crypto_btn": {
        "ru": "💵 Оплатить {n} USDT (крипто)",
        "es": "💵 Pagar {n} USDT (cripto)",
        "en": "💵 Pay {n} USDT (crypto)",
    },
    "pay_check_btn": {
        "ru": "✅ Я уже оплатил крипто",
        "es": "✅ Ya pagué con cripto",
        "en": "✅ I already paid crypto",
    },
    "payment_confirmed": {
        "ru": "🎉 *Оплата подтверждена!*\n\nПодписка активна на 30 дней. Продолжай вести учёт!\n\nПросто напиши или скажи что потратил/получил.",
        "es": "🎉 *¡Pago confirmado!*\n\nSuscripción activa por 30 días. ¡Sigue registrando!\n\nEscribe o di lo que gastaste/recibiste.",
        "en": "🎉 *Payment confirmed!*\n\nSubscription active for 30 days. Keep tracking!\n\nJust write or say what you spent/received.",
    },
    "payment_not_found": {
        "ru": "⏳ *Оплата ещё не поступила*\n\nПодожди 1-2 минуты и проверь снова.",
        "es": "⏳ *El pago aún no llegó*\n\nEspera 1-2 minutos y vuelve a verificar.",
        "en": "⏳ *Payment not received yet*\n\nWait 1-2 minutes and check again.",
    },

    # ── Категории ─────────────────────────────────────────────────────────────
    "cat_added": {
        "ru": "✅ Категория *{name}* добавлена!\n\nБот будет её распознавать автоматически.",
        "es": "✅ ¡Categoría *{name}* agregada!\n\nEl bot la reconocerá automáticamente.",
        "en": "✅ Category *{name}* added!\n\nThe bot will recognize it automatically.",
    },
    "cat_deleted": {
        "ru": "✅ Категория *{name}* удалена.",
        "es": "✅ Categoría *{name}* eliminada.",
        "en": "✅ Category *{name}* deleted.",
    },
    "cat_not_found": {
        "ru": "❌ Категория не найдена.",
        "es": "❌ Categoría no encontrada.",
        "en": "❌ Category not found.",
    },

    # ── Сброс ─────────────────────────────────────────────────────────────────
    "reset_confirm_msg": {
        "ru": "⚠️ *Удалить все твои записи?*\n\nЭто действие нельзя отменить.",
        "es": "⚠️ *¿Eliminar todos tus registros?*\n\nEsta acción no se puede deshacer.",
        "en": "⚠️ *Delete all your records?*\n\nThis cannot be undone.",
    },
    "reset_yes_btn": {
        "ru": "🗑 Да, удалить всё",
        "es": "🗑 Sí, eliminar todo",
        "en": "🗑 Yes, delete all",
    },
    "reset_no_btn": {
        "ru": "❌ Отмена",
        "es": "❌ Cancelar",
        "en": "❌ Cancel",
    },
    "reset_done": {
        "ru": "✅ Готово! Удалено *{n}* записей.",
        "es": "✅ ¡Listo! Se eliminaron *{n}* registros.",
        "en": "✅ Done! Deleted *{n}* records.",
    },
    "reset_cancelled": {
        "ru": "❌ Отменено. Записи сохранены.",
        "es": "❌ Cancelado. Registros conservados.",
        "en": "❌ Cancelled. Records kept.",
    },

    # ── Смена языка ───────────────────────────────────────────────────────────
    "change_language": {
        "ru": "🌐 Выбери язык:",
        "es": "🌐 Elige el idioma:",
        "en": "🌐 Choose language:",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    """Получить текст по ключу и языку"""
    lang = lang if lang in ("ru", "es", "en") else "ru"
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("ru", key))
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text
