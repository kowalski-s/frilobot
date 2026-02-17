"""Репозиторий для таблицы messages."""

from db.connection import get_supabase_client


class MessageRepository:
    """CRUD-операции для сообщений (шаблоны, отклики)."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._table = self._client.table("messages")

    def create(self, user_id: str, type: str, content: str,
               is_template: bool = False, metadata: dict | None = None) -> dict:
        """Создаёт новое сообщение."""
        data: dict = {
            "user_id": user_id,
            "type": type,
            "content": content,
            "is_template": is_template,
        }
        if metadata is not None:
            data["metadata"] = metadata
        response = self._table.insert(data).execute()
        return response.data[0]

    def get_by_id(self, message_id: str) -> dict | None:
        """Получает сообщение по id."""
        response = (
            self._table.select("*")
            .eq("id", message_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_user_templates(self, user_id: str) -> list[dict]:
        """Возвращает шаблоны пользователя."""
        response = (
            self._table.select("*")
            .eq("user_id", user_id)
            .eq("is_template", True)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def update_content(self, message_id: str, content: str) -> dict:
        """Обновляет текст сообщения."""
        response = (
            self._table.update({"content": content})
            .eq("id", message_id)
            .execute()
        )
        return response.data[0]

    def delete(self, message_id: str) -> None:
        """Удаляет сообщение."""
        self._table.delete().eq("id", message_id).execute()
