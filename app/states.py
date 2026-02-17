from aiogram.fsm.state import State, StatesGroup


class EntryState(StatesGroup):
    waiting_text = State()


class SettingsState(StatesGroup):
    waiting_daily_time = State()
    waiting_weekly_time = State()
    waiting_monthly_time = State()
