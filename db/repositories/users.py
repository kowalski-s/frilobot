"""Репозиторий для таблицы users."""

from db.connection import get_supabase_client


class UserRepository:
    """CRUD-операции для пользователей."""

    def __init__(self) -> None:
        self._client = get_supabase_client()
        self._table = self._client.table("users")

    def get_by_telegram_id(self, telegram_id: int) -> dict | None:
        """Находит пользователя по telegram_id."""
        response = (
            self._table.select("*")
            .eq("telegram_id", telegram_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_by_telegram_id_or_id(self, identifier: str | int) -> dict | None:
        """Находит пользователя по UUID (id) или telegram_id."""
        if isinstance(identifier, int):
            return self.get_by_telegram_id(identifier)
        # UUID — ищем по id
        response = (
            self._table.select("*")
            .eq("id", identifier)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def create(self, telegram_id: int, username: str | None = None, first_name: str | None = None) -> dict:
        """Создаёт нового пользователя."""
        data: dict = {"telegram_id": telegram_id}
        if username is not None:
            data["username"] = username
        if first_name is not None:
            data["first_name"] = first_name
        response = self._table.insert(data).execute()
        return response.data[0]

    def update(self, user_id: str, **fields) -> dict:
        """Обновляет поля пользователя."""
        fields["updated_at"] = "now()"
        response = self._table.update(fields).eq("id", user_id).execute()
        return response.data[0]

    def complete_onboarding(self, user_id: str) -> None:
        """Отмечает онбординг как пройденный."""
        self.update(user_id, onboarding_completed=True)

    def accept_disclaimer(self, user_id: str) -> None:
        """Отмечает принятие дисклеймера."""
        self.update(user_id, disclaimer_accepted=True)
