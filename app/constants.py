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
WEEKLY_TIME_UPDATED_TEMPLATE = (
    "Еженедельное время обновлено: {day} {time_value}"
)
MONTHLY_TIME_UPDATED_TEMPLATE = (
    "Ежемесячное время обновлено: {day} {time_value}"
)
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
SETTINGS_QUESTIONS_MENU_MESSAGE = "Управление ежедневными вопросами:"
QUESTIONS_LIST_HEADER = "Ежедневные вопросы:"
QUESTIONS_EMPTY_MESSAGE = "У вас пока нет ежедневных вопросов."
QUESTIONS_ADD_PROMPT = "Введите новый ежедневный вопрос одним сообщением."
QUESTIONS_DELETE_PROMPT = "Введите ID вопроса, который нужно удалить."
QUESTIONS_PAUSE_PROMPT = (
    "Введите ID вопроса, который нужно поставить на паузу."
)
QUESTIONS_RESUME_PROMPT = "Введите ID вопроса, который нужно возобновить."
QUESTIONS_INVALID_ID_MESSAGE = "Некорректный ID вопроса."
QUESTIONS_ADDED_MESSAGE = "Вопрос добавлен."
QUESTIONS_DELETED_MESSAGE = "Вопрос удалён."
QUESTIONS_PAUSED_MESSAGE = "Вопрос поставлен на паузу."
QUESTIONS_RESUMED_MESSAGE = "Вопрос снова активен."
QUESTIONS_NOT_FOUND_MESSAGE = "Вопрос не найден."
QUESTIONS_EMPTY_TEXT_MESSAGE = "Текст вопроса не должен быть пустым."
QUESTIONS_DUPLICATE_MESSAGE = "Такой вопрос уже есть в списке."
QUESTIONS_DEFAULT_TAG = "по умолчанию"
QUESTIONS_STATUS_ACTIVE = "активен"
QUESTIONS_STATUS_PAUSED = "на паузе"
QUESTIONS_RESET_DEFAULTS_MESSAGE = (
    "Список вопросов сброшен к значениям по умолчанию."
)
RECENT_ENTRIES_EMPTY = "У вас пока нет записей."
RECENT_ENTRIES_HEADER = "Последние 3 записи:"
MANAGE_ENTRIES_HEADER = "Последние записи (предпросмотр):"
MANAGE_ENTRIES_PROMPT = (
    "Введите индекс записи, которую хотите редактировать "
    "или удалить (например, d1)."
)
MANAGE_ENTRIES_EMPTY = "У вас пока нет записей для редактирования."
MANAGE_ENTRIES_MORE = "Показать ещё"
MANAGE_ENTRIES_ACTIONS_PROMPT = "Выберите действие с записью:"
MANAGE_ENTRIES_EDIT = "Редактировать"
MANAGE_ENTRIES_DELETE = "Удалить"
MANAGE_ENTRIES_TEXT_EDIT_PROMPT = (
    "Отправьте новый текст записи. Текущий текст уже подставлен в поле "
    "ввода — его можно сразу отредактировать и отправить."
)
MANAGE_ENTRIES_TEXT_EDIT_PLACEHOLDER_MAX = 64
MANAGE_ENTRIES_TEXT_EMPTY = "Текст записи не должен быть пустым."
MANAGE_ENTRIES_UPDATED = "Запись обновлена."
MANAGE_ENTRIES_DELETED = "Запись удалена."
MANAGE_ENTRIES_PAGE_END = "Больше записей нет."
MANAGE_ENTRIES_PREVIEW_LIMIT = 10
MANAGE_ENTRIES_PREVIEW_TEXT_LIMIT = 100
MANAGE_SHOW_MORE_PREFIX = "manage:page:"
MANAGE_EDIT_PREFIX = "manage:edit:"
MANAGE_DELETE_PREFIX = "manage:delete:"
MOOD_CALLBACK_PREFIX = "mood:"

ENTRY_MEDIA_MAX_IMAGES = 5
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ALLOWED_FILE_EXTENSIONS = {
    ".txt",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".rtf",
    ".odt",
}

ENTRY_UNSUPPORTED_EXTENSION_TEMPLATE = (
    "Файл с расширением {extension} недоступен для загрузки."
)
ENTRY_TOO_MANY_IMAGES_TEMPLATE = (
    "Можно прикрепить не более {max_images} изображений в одном сообщении."
)
ENTRY_EMPTY_CONTENT_MESSAGE = (
    "Отправьте текст записи, изображение или файл с поддерживаемым расширением."
)
EXPORT_VIEW_BY_INDEX = "Показать запись по индексу"
EXPORT_INDEX_CALLBACK = "export:index"
ENTRY_INDEX_PROMPT = "Введите индекс записи (например, d1):"
ENTRY_NOT_FOUND_TEMPLATE = "Запись с индексом {entry_index} не найдена."
ENTRY_DETAILS_HEADER_TEMPLATE = (
    "Запись {entry_index}\n"
    "Дата создания: {created_at}\n"
    "Тип: {entry_type}\n"
    "Дата записи: {entry_date}"
)
ENTRY_DETAILS_TEXT_TEMPLATE = "Текст: {text}"
ENTRY_DETAILS_ATTACHMENTS_HEADER = "Вложения:"
ENTRY_INDEX_INVALID_MESSAGE = "Индекс не должен быть пустым."
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
MENU_SETTINGS = "Настройки"
MENU_PAUSE = "Остановить напоминания"
MENU_RESUME = "Возобновить напоминания"
MENU_VIEW_ENTRIES = "Посмотреть записи"
MENU_MANAGE_ENTRIES = "Редактирование/удаление записей"
MENU_BACK = "Назад в главное меню"
MENU_DAILY = "Ежедневные напоминания"
MENU_WEEKLY = "Еженедельные напоминания"
MENU_MONTHLY = "Ежемесячные напоминания"
MENU_DAILY_QUESTIONS = "Ежедневные вопросы"
MENU_QUESTIONS_ADD = "Добавить вопрос"
MENU_QUESTIONS_DELETE = "Удалить вопрос"
MENU_QUESTIONS_PAUSE = "Пауза вопроса"
MENU_QUESTIONS_RESUME = "Возобновить вопрос"
MENU_QUESTIONS_RESET = "Сбросить к вопросам по умолчанию"

MOOD_GOOD_LABEL = "🟢 Хорошо"
MOOD_NEUTRAL_LABEL = "🟡 Нормально"
MOOD_BAD_LABEL = "🔴 Плохо"
MOOD_GOOD_ICON = "🟢"
MOOD_NEUTRAL_ICON = "🟡"
MOOD_BAD_ICON = "🔴"
