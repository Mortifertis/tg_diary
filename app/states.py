from aiogram.fsm.state import State, StatesGroup


class EntryState(StatesGroup):
    waiting_text = State()
    waiting_entry_index = State()
    waiting_manage_entry_index = State()
    waiting_manage_entry_edit_text = State()


class SettingsState(StatesGroup):
    waiting_daily_time = State()
    waiting_weekly_time = State()
    waiting_monthly_time = State()
    waiting_new_daily_question = State()
    waiting_delete_daily_question_id = State()
    waiting_pause_daily_question_id = State()
    waiting_resume_daily_question_id = State()
    waiting_daily_questions_count = State()
    waiting_language = State()
    waiting_toggle_icons_value = State()
    in_questions_menu = State()
    in_daily_questions_settings = State()
    in_appearance_settings = State()
    in_reminder_times_settings = State()
