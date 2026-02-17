"""Репозиторий для таблиц broadcasts и broadcast_items."""

from db.connection import get_supabase_client


class BroadcastRepository:
    """CRUD-операции для рассылок и их элементов."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._broadcasts = self._client.table("broadcasts")
        self._items = self._client.table("broadcast_items")

    def create(self, user_id: str, message_id: str, channel_ids: list[str]) -> dict:
        """Создаёт рассылку и элементы для каждого канала."""
        # Создаём запись рассылки
        bc_response = self._broadcasts.insert({
            "user_id": user_id,
            "message_id": message_id,
            "total_channels": len(channel_ids),
        }).execute()
        broadcast = bc_response.data[0]

        # Создаём элементы рассылки для каждого user_channel
        if channel_ids:
            items = [
                {"broadcast_id": broadcast["id"], "user_channel_id": ch_id}
                for ch_id in channel_ids
            ]
            self._items.insert(items).execute()

        return broadcast

    def get_active(self, user_id: str) -> dict | None:
        """Возвращает текущую активную рассылку пользователя."""
        response = (
            self._broadcasts.select("*")
            .eq("user_id", user_id)
            .in_("status", ["pending", "in_progress"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_history(self, user_id: str, limit: int = 10) -> list[dict]:
        """Возвращает историю рассылок пользователя."""
        response = (
            self._broadcasts.select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def update_status(self, broadcast_id: str, status: str) -> None:
        """Обновляет статус рассылки."""
        data: dict = {"status": status}
        if status == "in_progress":
            data["started_at"] = "now()"
        elif status in ("completed", "cancelled"):
            data["completed_at"] = "now()"
        self._broadcasts.update(data).eq("id", broadcast_id).execute()

    def get_pending_items(self, broadcast_id: str, limit: int = 1) -> list[dict]:
        """Возвращает следующие элементы для отправки."""
        response = (
            self._items.select("*, user_channels(*, channels(*))")
            .eq("broadcast_id", broadcast_id)
            .eq("status", "pending")
            .order("created_at")
            .limit(limit)
            .execute()
        )
        return response.data

    def mark_item_sent(self, item_id: str) -> None:
        """Отмечает элемент как отправленный."""
        self._items.update({
            "status": "sent",
            "sent_at": "now()",
        }).eq("id", item_id).execute()

    def mark_item_failed(self, item_id: str, error: str) -> None:
        """Отмечает элемент как ошибочный."""
        self._items.update({
            "status": "failed",
            "error_message": error,
        }).eq("id", item_id).execute()

    def increment_sent_count(self, broadcast_id: str) -> None:
        """Увеличивает счётчик отправленных на 1."""
        response = (
            self._broadcasts.select("sent_count")
            .eq("id", broadcast_id)
            .limit(1)
            .execute()
        )
        current = response.data[0]["sent_count"]
        self._broadcasts.update({"sent_count": current + 1}).eq("id", broadcast_id).execute()

    def increment_error_count(self, broadcast_id: str) -> None:
        """Увеличивает счётчик ошибок на 1."""
        response = (
            self._broadcasts.select("error_count")
            .eq("id", broadcast_id)
            .limit(1)
            .execute()
        )
        current = response.data[0]["error_count"]
        self._broadcasts.update({"error_count": current + 1}).eq("id", broadcast_id).execute()
