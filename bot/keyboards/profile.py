"""Клавиатуры для модуля «Мой профиль»."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.pagination import MenuCallback


class ProfileCallback(CallbackData, prefix="prof"):
    """Callback для кнопок профиля."""

    action: str
    value: str = ""


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура профиля: редактирование полей + возврат."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Специализации",
            callback_data=ProfileCallback(action="edit", value="specializations").pack(),
        )],
        [InlineKeyboardButton(
            text="Описание услуг",
            callback_data=ProfileCallback(action="edit", value="services").pack(),
        )],
        [InlineKeyboardButton(
            text="Параметры поиска",
            callback_data=ProfileCallback(action="edit", value="search").pack(),
        )],
        [InlineKeyboardButton(
            text="\u2190 Меню",
            callback_data=MenuCallback(action="main").pack(),
        )],
    ])


def get_profile_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в профиль."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2190 Профиль",
            callback_data=ProfileCallback(action="back").pack(),
        )],
    ])
