"""Сервис «Радар» — поиск каналов и управление подключениями."""

import logging
import re

from db.repositories.channels import ChannelRepository
from parsers.tgstat import TgstatParser

logger = logging.getLogger(__name__)

# Слова-маркеры для фильтрации: каналы/чаты с вакансиями, работой, фрилансом
_RELEVANCE_MARKERS = re.compile(
    r"вакансии|работа|заказ|фриланс|freelance|job|hire|ищем|ищу|"
    r"нужен|требуется|удалённ|удаленн|remote|recruiting|"
    r"подработк|тендер|аутсорс|outsourc",
    re.IGNORECASE,
)

# Контекстные слова, которые добавляются к поисковому запросу
_SEARCH_CONTEXT = "вакансии фриланс работа заказы"


class RadarService:
    """Бизнес-логика поиска и подключения каналов."""

    def __init__(self) -> None:
        self._parser = TgstatParser()
        self._repo = ChannelRepository()

    async def search_channels(self, query: str, limit: int = 20) -> list[dict]:
        """Ищет каналы с вакансиями/работой, сохраняет в БД, возвращает список.

        К запросу автоматически добавляются контекстные слова (вакансии, фриланс...).
        Результаты фильтруются по наличию маркеров релевантности в названии/описании.
        """
        # Добавляем контекст к запросу
        enriched_query = f"{query} {_SEARCH_CONTEXT}"
        parsed = await self._parser.search(enriched_query, limit=limit * 3)
        if not parsed:
            return []

        channels: list[dict] = []
        for item in parsed:
            username = item.get("username")
            if not username:
                continue

            # Фильтруем: оставляем только каналы с маркерами релевантности
            if not self._is_relevant(item):
                continue

            channel = self._repo.get_or_create_by_username(
                username=username,
                title=item.get("title"),
                description=item.get("description"),
                subscribers_count=item.get("subscribers_count"),
                category=item.get("category"),
            )
            channels.append(channel)
            if len(channels) >= limit:
                break

        logger.info("Radar search: %d relevant channels for query=%r", len(channels), query)
        return channels

    @staticmethod
    def _is_relevant(item: dict) -> bool:
        """Проверяет, содержит ли канал маркеры релевантности (вакансии, работа и т.д.)."""
        text = " ".join(filter(None, [
            item.get("title", ""),
            item.get("description", ""),
            item.get("username", ""),
            item.get("category", ""),
        ]))
        return bool(_RELEVANCE_MARKERS.search(text))

    def get_user_channels(self, user_id: str) -> list[dict]:
        """Возвращает подключённые каналы пользователя."""
        return self._repo.get_user_channels(user_id)

    def link_channel(self, user_id: str, channel_id: str, purpose: str) -> dict | None:
        """Подключает канал к пользователю. Пропускает, если уже привязан."""
        existing = self._repo.get_user_channel(user_id, channel_id)
        if existing:
            return existing
        return self._repo.link_to_user(user_id, channel_id, purpose)

    def unlink_channel(self, user_id: str, channel_id: str) -> None:
        """Отключает канал от пользователя."""
        self._repo.unlink_from_user(user_id, channel_id)

    def update_channel_purpose(self, user_channel_id: str, purpose: str) -> dict:
        """Изменяет назначение канала."""
        return self._repo.update_user_channel_purpose(user_channel_id, purpose)
