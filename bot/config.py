"""Конфигурация бота. Загрузка настроек из переменных окружения."""

from dataclasses import dataclass, field
from os import getenv
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _parse_admin_ids(raw: str) -> list[int]:
    """Парсит строку вида '123,456' в список int."""
    if not raw:
        return []
    return [int(id_.strip()) for id_ in raw.split(",") if id_.strip()]


@dataclass(frozen=True)
class Settings:
    """Настройки приложения из переменных окружения."""

    # Telegram
    bot_token: str
    admin_ids: list[int]

    # Supabase (MVP)
    supabase_url: str
    supabase_key: str

    # LLM
    llm_api_key: str = ""
    llm_model: str = ""

    # Рассылка (дефолты)
    default_broadcast_limit: int = 5
    default_min_delay: int = 30
    default_max_delay: int = 120


def _load_settings() -> Settings:
    """Загружает настройки из переменных окружения."""
    bot_token = getenv("BOT_TOKEN", "")
    if not bot_token:
        raise ValueError("BOT_TOKEN не задан. Заполни .env файл (см. .env.example).")

    supabase_url = getenv("SUPABASE_URL", "")
    supabase_key = getenv("SUPABASE_KEY", "")
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL и SUPABASE_KEY должны быть заданы в .env.")

    return Settings(
        bot_token=bot_token,
        admin_ids=_parse_admin_ids(getenv("ADMIN_IDS", "")),
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        llm_api_key=getenv("LLM_API_KEY", ""),
        llm_model=getenv("LLM_MODEL", ""),
        default_broadcast_limit=int(getenv("DEFAULT_BROADCAST_LIMIT", "5")),
        default_min_delay=int(getenv("DEFAULT_MIN_DELAY", "30")),
        default_max_delay=int(getenv("DEFAULT_MAX_DELAY", "120")),
    )


settings = _load_settings()
