"""Мидлварь авторизации — регистрирует пользователя и кладёт его в data."""

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from db.repositories.settings import SettingsRepository
from db.repositories.users import UserRepository

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """При каждом обновлении находит или создаёт пользователя в БД."""

    def __init__(self) -> None:
        self._user_repo = UserRepository()
        self._settings_repo = SettingsRepository()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # aiogram кладёт telegram-пользователя в event_from_user через UserContextMiddleware
        tg_user: User | None = data.get("event_from_user")

        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        # Ищем пользователя в БД
        user = self._user_repo.get_by_telegram_id(tg_user.id)

        if user is None:
            # Регистрируем нового пользователя
            logger.info("New user registered: telegram_id=%d, username=%s", tg_user.id, tg_user.username)
            user = self._user_repo.create(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
            )
            # Создаём дефолтные настройки
            self._settings_repo.create_default(user_id=user["id"])

        data["user"] = user
        return await handler(event, data)
