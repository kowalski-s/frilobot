"""Репозиторий для таблицы settings."""

from db.connection import get_supabase_client


class SettingsRepository:
    """CRUD-операции для пользовательских настроек."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._table = self._client.table("settings")

    def get_by_user_id(self, user_id: str) -> dict | None:
        """Получает настройки пользователя."""
        response = (
            self._table.select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def create_default(self, user_id: str) -> dict:
        """Создаёт запись с дефолтными значениями."""
        response = self._table.insert({"user_id": user_id}).execute()
        return response.data[0]

    def update(self, user_id: str, **fields) -> dict:
        """Обновляет настройки пользователя."""
        fields["updated_at"] = "now()"
        response = self._table.update(fields).eq("user_id", user_id).execute()
        return response.data[0]
