"""Мидлварь антифлуда — не более 1 сообщения в секунду от пользователя."""

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User


class ThrottlingMiddleware(BaseMiddleware):
    """Игнорирует обновления, если пользователь шлёт чаще раза в секунду."""

    def __init__(self, rate_limit: float = 1.0) -> None:
        self._rate_limit = rate_limit
        self._last_time: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: User | None = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_time.get(tg_user.id, 0.0)

        if now - last < self._rate_limit:
            # Слишком быстро — игнорируем
            return None

        self._last_time[tg_user.id] = now
        return await handler(event, data)
