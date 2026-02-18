"""Клавиатуры для модуля «Настройки»."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.pagination import MenuCallback


# Префикс для callback data настроек
_PREFIX = "sett"


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек: редактирование полей + возврат."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Лимит рассылки",
            callback_data=f"{_PREFIX}:edit:limit",
        )],
        [InlineKeyboardButton(
            text="Тихие часы",
            callback_data=f"{_PREFIX}:edit:quiet",
        )],
        [InlineKeyboardButton(
            text="Задержки между сообщениями",
            callback_data=f"{_PREFIX}:edit:delays",
        )],
        [InlineKeyboardButton(
            text="\u2190 Меню",
            callback_data=MenuCallback(action="main").pack(),
        )],
    ])


def get_limit_keyboard(current: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура выбора лимита рассылки в час."""
    options = [3, 5, 10, 15]
    buttons = []
    for val in options:
        label = f"\u2705 {val}" if val == current else str(val)
        buttons.append(InlineKeyboardButton(
            text=label,
            callback_data=f"{_PREFIX}:limit:{val}",
        ))
    return InlineKeyboardMarkup(inline_keyboard=[
        buttons,
        [InlineKeyboardButton(
            text="\u2190 Настройки",
            callback_data=f"{_PREFIX}:back:",
        )],
    ])


def get_settings_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в настройки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2190 Настройки",
            callback_data=f"{_PREFIX}:back:",
        )],
    ])
