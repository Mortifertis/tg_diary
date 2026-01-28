from aiogram.fsm.state import State, StatesGroup


class EntryState(StatesGroup):
    waiting_text = State()
