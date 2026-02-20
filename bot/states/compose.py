"""FSM-состояния для модуля «Составить текст» (чат-формат)."""

from aiogram.fsm.state import State, StatesGroup


class ComposeState(StatesGroup):
    """Состояния чат-режима генерации текста."""

    collecting_broadcast_info = State()  # Сбор инфо для рассылки (чат с ИИ)
    collecting_vacancy_info = State()    # Сбор инфо для отклика (чат с ИИ)
    refining = State()                   # Доработка сгенерированного текста
