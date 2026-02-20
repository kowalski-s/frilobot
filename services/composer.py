"""Сервис «Составить текст» — генерация сообщений через LLM в чат-режиме."""

import logging

from db.repositories.messages import MessageRepository
from db.repositories.users import UserRepository
from llm.client import get_llm_client
from llm.prompts.broadcast_message import (
    build_context_message as build_broadcast_context,
    build_system_prompt as build_broadcast_system,
)
from llm.prompts.vacancy_response import (
    build_context_message as build_vacancy_context,
    build_system_prompt as build_vacancy_system,
)

logger = logging.getLogger(__name__)


class ComposerService:
    """Бизнес-логика генерации текстов через LLM (чат-режим)."""

    def __init__(self) -> None:
        self._users = UserRepository()
        self._messages = MessageRepository()

    async def generate_broadcast(
        self,
        user_id: str,
        chat_history: list[dict],
        length: str = "medium",
    ) -> str:
        """Генерирует рассылочное сообщение с учётом истории диалога.

        Args:
            user_id: ID пользователя в БД
            chat_history: история сообщений [{"role": ..., "content": ...}]
            length: длина сообщения (short / medium / long)

        Returns:
            Текст ответа ИИ
        """
        system_prompt = build_broadcast_system(length)
        messages = [{"role": "system", "content": system_prompt}] + chat_history

        client = get_llm_client()
        result = await client.generate_chat(messages=messages)
        logger.info("Generated broadcast for user=%s, history_len=%d", user_id, len(chat_history))
        return result

    async def generate_broadcast_from_profile(
        self,
        user_id: str,
        length: str = "medium",
    ) -> tuple[str, list[dict]]:
        """Генерирует рассылку на основе профиля (без предварительного диалога).

        Returns:
            (текст ответа, начальная история чата)
        """
        user = self._users.get_by_telegram_id_or_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        context_msg = build_broadcast_context(user)
        chat_history = [{"role": "user", "content": context_msg}]

        result = await self.generate_broadcast(user_id, chat_history, length)
        chat_history.append({"role": "assistant", "content": result})
        return result, chat_history

    async def generate_vacancy_response(
        self,
        user_id: str,
        chat_history: list[dict],
    ) -> str:
        """Генерирует отклик на вакансию с учётом истории диалога.

        Args:
            user_id: ID пользователя в БД
            chat_history: история сообщений

        Returns:
            Текст ответа ИИ
        """
        system_prompt = build_vacancy_system()
        messages = [{"role": "system", "content": system_prompt}] + chat_history

        client = get_llm_client()
        result = await client.generate_chat(messages=messages)
        logger.info("Generated vacancy response for user=%s", user_id)
        return result

    async def init_vacancy_chat(self, user_id: str) -> list[dict]:
        """Инициализирует чат для отклика — подкладывает профиль.

        Returns:
            Начальная история с контекстом профиля
        """
        user = self._users.get_by_telegram_id_or_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        context_msg = build_vacancy_context(user)
        return [{"role": "user", "content": context_msg}]

    async def refine(
        self,
        user_id: str,
        chat_history: list[dict],
        msg_type: str = "broadcast",
        length: str = "medium",
    ) -> str:
        """Доработка: пользователь написал инструкцию → перегенерация.

        Args:
            user_id: ID пользователя
            chat_history: полная история с последним сообщением пользователя
            msg_type: broadcast / vacancy
            length: длина (для broadcast)

        Returns:
            Текст доработанного ответа
        """
        if msg_type == "broadcast":
            return await self.generate_broadcast(user_id, chat_history, length)
        else:
            return await self.generate_vacancy_response(user_id, chat_history)

    def save_as_template(self, user_id: str, content: str, msg_type: str = "broadcast") -> dict:
        """Сохраняет текст как шаблон."""
        return self._messages.create(
            user_id=user_id,
            type=msg_type,
            content=content,
            is_template=True,
        )

    def get_templates(self, user_id: str) -> list[dict]:
        """Возвращает шаблоны пользователя."""
        return self._messages.get_user_templates(user_id)

    def delete_template(self, message_id: str) -> None:
        """Удаляет шаблон."""
        self._messages.delete(message_id)
