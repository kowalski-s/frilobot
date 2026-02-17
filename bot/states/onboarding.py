"""FSM-состояния онбординга."""

from aiogram.fsm.state import State, StatesGroup


class OnboardingState(StatesGroup):
    """7 шагов онбординга нового пользователя."""

    welcome = State()
    specialization = State()
    specialization_custom = State()
    services = State()
    search_keywords = State()
    search_budget = State()
    search_format = State()
    disclaimer = State()
