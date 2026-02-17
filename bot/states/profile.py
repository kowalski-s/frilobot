"""FSM-состояния для редактирования профиля."""

from aiogram.fsm.state import State, StatesGroup


class ProfileEditState(StatesGroup):
    """Состояния редактирования полей профиля."""

    editing_specializations = State()
    editing_specialization_custom = State()
    editing_services = State()
    editing_keywords = State()
    editing_budget = State()
    editing_format = State()
