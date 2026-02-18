from __future__ import annotations

BOT_TOKEN_MISSING = "BOT_TOKEN is not set"

START_MESSAGE = (
    "Я дневник-бот. Буду писать первым и просить короткие заметки.\n"
    "Теперь можно пользоваться меню кнопок ниже."
)
NEED_START_MESSAGE = "Сначала напишите /start."

MOOD_SAVED_MESSAGE = "Настроение сохранено."
ENTRY_SAVED_MESSAGE = "Сохранено. Спасибо!"

TIME_USAGE_MESSAGE = "Укажи время: HH:MM"
WEEKLY_USAGE_MESSAGE = "Укажи день недели и время: 6 20:00 (0=пн, 6=вс)"
MONTHLY_USAGE_MESSAGE = "Укажи день месяца и время: 1 20:00"

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
MANUAL_ENTRY_PROMPT = (
    "Готов выслушать тебя. Напиши новую запись одним сообщением."
)

SETTINGS_MENU_MESSAGE = "Выберите, что настроить:"
SETTINGS_DAILY_PROMPT = "Введите ежедневное время в формате HH:MM"
SETTINGS_WEEKLY_PROMPT = "Введите день и время в формате: 0-6 HH:MM"
SETTINGS_MONTHLY_PROMPT = "Введите день месяца и время в формате: 1-31 HH:MM"
RECENT_ENTRIES_EMPTY = "У вас пока нет записей."
RECENT_ENTRIES_HEADER = "Последние 3 записи:"
EXPORT_CAPTION = "Полный архив записей за всё время."
EXPORT_MENU_PROMPT = "Выберите период для выгрузки архива:"
EXPORT_WEEK = "Последняя неделя"
EXPORT_MONTH = "Последний месяц"
EXPORT_3_MONTHS = "Последние 3 месяца"
EXPORT_YEAR = "Последний год"
EXPORT_ALL = "За всё время"
EXPORT_BACK = "Назад"
EXPORT_CALLBACK_PREFIX = "export:"
EXPORT_DONE_TEMPLATE = "Архив записей ({period_label})."
EXPORT_NO_ENTRIES = "За выбранный период записей нет."

MENU_CREATE_ENTRY = "Сделать новую запись"
MENU_SET_REMINDERS = "Установить время напоминаний"
MENU_PAUSE = "Остановить напоминания"
MENU_RESUME = "Возобновить напоминания"
MENU_VIEW_ENTRIES = "Посмотреть записи"
MENU_BACK = "Назад в главное меню"
MENU_DAILY = "Ежедневные"
MENU_WEEKLY = "Еженедельные"
MENU_MONTHLY = "Ежемесячные"

MOOD_GOOD_LABEL = "🟢 Хорошо"
MOOD_NEUTRAL_LABEL = "🟡 Нормально"
MOOD_BAD_LABEL = "🔴 Плохо"
MOOD_GOOD_ICON = "🟢"
MOOD_NEUTRAL_ICON = "🟡"
MOOD_BAD_ICON = "🔴"
