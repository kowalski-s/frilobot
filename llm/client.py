"""LLM-клиент. Единая точка для всех запросов к языковой модели.

Использует OpenAI-совместимый API (NeuroAPI, OpenAI, и т.д.).
Смена провайдера — замена base_url в .env.
"""

import logging
from typing import Any

from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, RateLimitError

from bot.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Асинхронный клиент для OpenAI-совместимого API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.llm_api_key
        self._base_url = base_url or settings.llm_base_url
        self._model = model or settings.llm_model

        if not self._api_key:
            raise ValueError("LLM_API_KEY не задан. Заполни .env файл.")

        self._client = AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=60.0,
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Один запрос к LLM. Возвращает текст ответа."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned empty response")
            return content.strip()

        except APITimeoutError:
            logger.error("LLM request timed out")
            raise
        except RateLimitError:
            logger.error("LLM rate limit exceeded")
            raise
        except APIConnectionError:
            logger.error("LLM connection error")
            raise
        except Exception:
            logger.exception("LLM unexpected error")
            raise

    async def generate_variants(
        self,
        system_prompt: str,
        user_prompt: str,
        count: int = 3,
        temperature: float = 0.8,
        max_tokens: int = 2000,
    ) -> list[str]:
        """Генерирует несколько вариантов текста.

        Делает count отдельных запросов с повышенной temperature.
        """
        variants: list[str] = []
        for i in range(count):
            try:
                result = await self.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                variants.append(result)
            except Exception:
                logger.warning("Failed to generate variant %d/%d", i + 1, count)
                # Продолжаем генерацию остальных вариантов
                continue

        if not variants:
            raise RuntimeError("Не удалось сгенерировать ни одного варианта")

        return variants

    async def generate_chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Запрос к LLM с полной историей диалога.

        Args:
            messages: список сообщений [{"role": "system/user/assistant", "content": "..."}]
            temperature: креативность
            max_tokens: максимум токенов ответа

        Returns:
            Текст ответа ассистента
        """
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned empty response")
            return content.strip()

        except APITimeoutError:
            logger.error("LLM chat request timed out")
            raise
        except RateLimitError:
            logger.error("LLM rate limit exceeded")
            raise
        except APIConnectionError:
            logger.error("LLM connection error")
            raise
        except Exception:
            logger.exception("LLM unexpected error")
            raise

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> str:
        """Запрос с ожиданием JSON-ответа. Низкая temperature для стабильности."""
        return await self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# Singleton-экземпляр
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Возвращает singleton LLM-клиент."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
