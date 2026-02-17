"""Репозиторий для таблиц channel_messages и saved_vacancies."""

from db.connection import get_supabase_client


class VacancyRepository:
    """CRUD-операции для сообщений каналов и сохранённых вакансий."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._messages = self._client.table("channel_messages")
        self._saved = self._client.table("saved_vacancies")

    def save_channel_messages(self, channel_id: str, messages: list[dict]) -> int:
        """Bulk upsert сообщений канала. Возвращает количество обработанных."""
        if not messages:
            return 0

        rows = [
            {
                "channel_id": channel_id,
                "telegram_message_id": msg["telegram_message_id"],
                "text": msg.get("text"),
                "date": msg.get("date"),
            }
            for msg in messages
        ]

        # Upsert по уникальному ключу (channel_id, telegram_message_id)
        response = (
            self._messages.upsert(
                rows,
                on_conflict="channel_id,telegram_message_id",
            ).execute()
        )
        return len(response.data)

    def get_unfiltered(self, channel_ids: list[str], limit: int = 100) -> list[dict]:
        """Возвращает сообщения, которые ещё не проверены (is_vacancy IS NULL)."""
        response = (
            self._messages.select("*")
            .in_("channel_id", channel_ids)
            .is_("is_vacancy", "null")
            .order("date", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def mark_as_vacancy(self, message_id: str, vacancy_data: dict) -> None:
        """Отмечает сообщение как вакансию с данными."""
        self._messages.update({
            "is_vacancy": True,
            "vacancy_data": vacancy_data,
        }).eq("id", message_id).execute()

    def mark_as_not_vacancy(self, message_id: str) -> None:
        """Отмечает сообщение как не-вакансию."""
        self._messages.update({"is_vacancy": False}).eq("id", message_id).execute()

    def get_vacancies(self, channel_ids: list[str], limit: int = 10) -> list[dict]:
        """Возвращает подтверждённые вакансии из указанных каналов."""
        response = (
            self._messages.select("*")
            .in_("channel_id", channel_ids)
            .eq("is_vacancy", True)
            .order("date", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def save_vacancy(self, user_id: str, channel_message_id: str) -> dict:
        """Сохраняет вакансию в избранное."""
        response = self._saved.insert({
            "user_id": user_id,
            "channel_message_id": channel_message_id,
        }).execute()
        return response.data[0]

    def get_saved(self, user_id: str) -> list[dict]:
        """Возвращает сохранённые вакансии пользователя."""
        response = (
            self._saved.select("*, channel_messages(*)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def update_saved_status(self, saved_id: str, status: str,
                            response_text: str | None = None) -> None:
        """Обновляет статус сохранённой вакансии."""
        data: dict = {"status": status}
        if response_text is not None:
            data["response_text"] = response_text
        self._saved.update(data).eq("id", saved_id).execute()
