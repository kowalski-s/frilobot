"""Callback data factories для навигации и пагинации."""

from aiogram.filters.callback_data import CallbackData


class MenuCallback(CallbackData, prefix="menu"):
    """Callback для кнопок главного меню."""

    action: str


class PageCallback(CallbackData, prefix="page"):
    """Callback для пагинации."""

    section: str
    page: int
