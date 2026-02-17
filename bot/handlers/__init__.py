"""Регистрация всех роутеров хендлеров."""

from aiogram import Dispatcher

from bot.handlers.menu import router as menu_router
from bot.handlers.profile import router as profile_router
from bot.handlers.start import router as start_router


def register_all_handlers(dp: Dispatcher) -> None:
    """Подключает все роутеры к диспетчеру."""
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(menu_router)
