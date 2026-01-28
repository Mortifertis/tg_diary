from __future__ import annotations

BOT_TOKEN_MISSING = "BOT_TOKEN is not set"

START_MESSAGE = (
    "Я дневник-бот. Буду писать первым и просить короткие заметки.\n"
    "Команды: /time, /weekly, /monthly, /pause, /resume, /stats."
)
NEED_START_MESSAGE = "Сначала напишите /start."

MOOD_SAVED_MESSAGE = "Настроение сохранено."
ENTRY_SAVED_MESSAGE = "Сохранено. Спасибо!"

TIME_USAGE_MESSAGE = "Укажи время: /time HH:MM"
WEEKLY_USAGE_MESSAGE = "Укажи день недели и время: /weekly 6 20:00 (0=пн, 6=вс)"
MONTHLY_USAGE_MESSAGE = "Укажи день месяца и время: /monthly 1 20:00"

DAILY_TIME_UPDATED_TEMPLATE = "Ежедневное время обновлено: {time_value}"
WEEKLY_TIME_UPDATED_TEMPLATE = "Еженедельное время обновлено: {day} {time_value}"
MONTHLY_TIME_UPDATED_TEMPLATE = "Ежемесячное время обновлено: {day} {time_value}"
PAUSE_ENABLED_TEMPLATE = "Пауза включена до {pause_until}."
PAUSE_DISABLED_MESSAGE = "Пауза снята."

STATS_TOTAL_TEMPLATE = "{total} записей всего"
STATS_STREAK_TEMPLATE = "Серия: {streak} дней подряд"
STATS_MOOD_TEMPLATE = "Настроение: {mood_line}"

STATUS_HEADER = "Текущие настройки:"
STATUS_DAILY_TEMPLATE = "День: {daily_time}"
STATUS_WEEKLY_TEMPLATE = "Неделя: {weekly_day} {weekly_time}"
STATUS_MONTHLY_TEMPLATE = "Месяц: {monthly_day} {monthly_time}"
STATUS_PAUSE_TEMPLATE = "Статус: {pause}"
STATUS_PAUSE_ACTIVE_TEMPLATE = "пауза до {pause_until}"
STATUS_PAUSE_INACTIVE = "активен"

DAILY_PROMPT_SUFFIX = "Можно коротко, 1–3 предложения."
WEEKLY_PROMPT_PREFIX = "Еженедельная заметка."
MONTHLY_PROMPT_PREFIX = "Месячная ретроспектива."

MOOD_GOOD_LABEL = "🟢 Хорошо"
MOOD_NEUTRAL_LABEL = "🟡 Нормально"
MOOD_BAD_LABEL = "🔴 Плохо"
MOOD_GOOD_ICON = "🟢"
MOOD_NEUTRAL_ICON = "🟡"
MOOD_BAD_ICON = "🔴"
