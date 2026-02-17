"""Клавиатура главного меню."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.pagination import MenuCallback


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Возвращает inline-клавиатуру главного меню (6 кнопок, 2 колонки)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Радар",
                callback_data=MenuCallback(action="radar").pack(),
            ),
            InlineKeyboardButton(
                text="Составить текст",
                callback_data=MenuCallback(action="compose").pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Найти заказы",
                callback_data=MenuCallback(action="vacancies").pack(),
            ),
            InlineKeyboardButton(
                text="Рассылка",
                callback_data=MenuCallback(action="broadcast").pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Мой профиль",
                callback_data=MenuCallback(action="profile").pack(),
            ),
            InlineKeyboardButton(
                text="Настройки",
                callback_data=MenuCallback(action="settings").pack(),
            ),
        ],
    ])
