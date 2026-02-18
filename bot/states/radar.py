"""FSM-состояния для модуля «Радар»."""

from aiogram.fsm.state import State, StatesGroup


class RadarState(StatesGroup):
    """Состояния при работе с радаром."""

    searching = State()          # Ввод поискового запроса
    browsing_results = State()   # Просмотр результатов поиска (карточки)
