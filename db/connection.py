"""Подключение к Supabase. Singleton-клиент для всего приложения."""

from supabase import Client, create_client

from bot.config import settings

_client: Client | None = None


def get_supabase_client() -> Client:
    """Возвращает клиент Supabase (singleton)."""
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
