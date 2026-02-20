"""Репозиторий для таблиц channels и user_channels."""

from db.connection import get_supabase_client


class ChannelRepository:
    """CRUD-операции для каналов и связей с пользователями."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._channels = self._client.table("channels")
        self._user_channels = self._client.table("user_channels")

    def get_or_create(self, telegram_id: int, username: str | None = None,
                      title: str | None = None, **kwargs) -> dict:
        """Возвращает канал по telegram_id или создаёт новый."""
        response = (
            self._channels.select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]

        data: dict = {"telegram_id": telegram_id}
        if username is not None:
            data["username"] = username
        if title is not None:
            data["title"] = title
        data.update(kwargs)
        response = self._channels.insert(data).execute()
        return response.data[0]

    def get_or_create_by_username(self, username: str, **kwargs) -> dict:
        """Возвращает канал по username или создаёт новый."""
        existing = self.get_by_username(username)
        if existing:
            return existing
        data: dict = {"username": username, "source": "tgstat"}
        data.update(kwargs)
        response = self._channels.insert(data).execute()
        return response.data[0]

    def get_user_channel(self, user_id: str, channel_id: str) -> dict | None:
        """Возвращает связь пользователя с каналом."""
        response = (
            self._user_channels.select("*")
            .eq("user_id", user_id)
            .eq("channel_id", channel_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_by_id(self, channel_id: str) -> dict | None:
        """Находит канал по id."""
        response = (
            self._channels.select("*")
            .eq("id", channel_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_by_username(self, username: str) -> dict | None:
        """Находит канал по username."""
        response = (
            self._channels.select("*")
            .eq("username", username)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def update(self, channel_id: str, **fields) -> dict:
        """Обновляет поля канала."""
        response = self._channels.update(fields).eq("id", channel_id).execute()
        return response.data[0]

    def link_to_user(self, user_id: str, channel_id: str, purpose: str) -> dict:
        """Привязывает канал к пользователю (создаёт запись в user_channels)."""
        response = self._user_channels.insert({
            "user_id": user_id,
            "channel_id": channel_id,
            "purpose": purpose,
        }).execute()
        return response.data[0]

    def unlink_from_user(self, user_id: str, channel_id: str) -> None:
        """Отвязывает канал от пользователя."""
        self._user_channels.delete().eq("user_id", user_id).eq("channel_id", channel_id).execute()

    def get_user_channels(self, user_id: str, purpose: str | None = None) -> list[dict]:
        """Возвращает каналы пользователя, опционально фильтр по purpose."""
        query = (
            self._user_channels.select("*, channels(*)")
            .eq("user_id", user_id)
            .eq("is_active", True)
        )
        if purpose is not None:
            query = query.eq("purpose", purpose)
        response = query.execute()
        return response.data

    def update_user_channel_purpose(self, user_channel_id: str, purpose: str) -> dict:
        """Обновляет назначение связи пользователя с каналом."""
        response = (
            self._user_channels.update({"purpose": purpose})
            .eq("id", user_channel_id)
            .execute()
        )
        return response.data[0]
