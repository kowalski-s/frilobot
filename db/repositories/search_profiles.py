"""Репозиторий для таблицы search_profiles."""

from db.connection import get_supabase_client


class SearchProfileRepository:
    """CRUD-операции для профилей поиска вакансий."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._table = self._client.table("search_profiles")

    def create(self, user_id: str, keywords: list[str],
               min_budget: int | None = None,
               work_format: list[str] | None = None) -> dict:
        """Создаёт новый профиль поиска."""
        data: dict = {
            "user_id": user_id,
            "keywords": keywords,
        }
        if min_budget is not None:
            data["min_budget"] = min_budget
        if work_format is not None:
            data["work_format"] = work_format
        response = self._table.insert(data).execute()
        return response.data[0]

    def get_active(self, user_id: str) -> dict | None:
        """Возвращает активный профиль поиска пользователя."""
        response = (
            self._table.select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def update(self, profile_id: str, **fields) -> dict:
        """Обновляет поля профиля поиска."""
        response = self._table.update(fields).eq("id", profile_id).execute()
        return response.data[0]
