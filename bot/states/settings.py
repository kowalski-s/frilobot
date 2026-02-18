"""FSM-состояния для редактирования настроек."""

from aiogram.fsm.state import State, StatesGroup


class SettingsEditState(StatesGroup):
    """Состояния редактирования настроек."""

    editing_quiet_hours = State()
    editing_delays = State()
