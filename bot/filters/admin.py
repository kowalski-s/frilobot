"""Фильтр админа — пропускает только администраторов бота."""

from aiogram.filters import Filter
from aiogram.types import TelegramObject

from bot.config import settings


class IsAdmin(Filter):
    """Проверяет, является ли пользователь админом."""

    async def __call__(self, event: TelegramObject, user: dict | None = None, **kwargs) -> bool:
        if user is None:
            return False

        # Проверяем флаг в БД или наличие telegram_id в ADMIN_IDS
        if user.get("is_admin"):
            return True

        return user.get("telegram_id") in settings.admin_ids
