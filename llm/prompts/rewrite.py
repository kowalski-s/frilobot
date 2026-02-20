"""Промпт для уникализации текста.

Рерайт сообщения перед рассылкой — чтобы каждое отправленное сообщение
было уникальным и не выглядело как спам.
"""


def build_prompt(
    original_text: str,
    channel_info: dict | None = None,
) -> tuple[str, str]:
    """Строит system + user промпт для уникализации текста.

    Args:
        original_text: исходный текст для рерайта
        channel_info: информация о канале (title, description) — для адаптации

    Returns:
        (system_prompt, user_prompt)
    """
    system_prompt = (
        "Ты — копирайтер-рерайтер. Твоя задача — переписать текст так, "
        "чтобы он сохранил смысл и посыл, но отличался по формулировкам.\n\n"
        "ПРАВИЛА:\n"
        "1. Сохрани основной смысл и призыв к действию.\n"
        "2. Измени порядок предложений, замени синонимами, перефразируй.\n"
        "3. Сохрани длину — не делай текст значительно длиннее или короче.\n"
        "4. Сохрани тон и стиль оригинала.\n"
        "5. НЕ добавляй новую информацию, которой нет в оригинале.\n"
        "6. НЕ удаляй ключевую информацию (контакты, навыки, предложение).\n"
        "7. Результат должен выглядеть как новое сообщение, а не как правка старого.\n"
        "8. Отвечай ТОЛЬКО текстом переписанного сообщения, без пояснений."
    )

    user_parts = [
        "ОРИГИНАЛЬНЫЙ ТЕКСТ:",
        original_text.strip(),
    ]

    if channel_info:
        channel_title = channel_info.get("title") or channel_info.get("username") or ""
        channel_desc = channel_info.get("description") or ""
        if channel_title:
            user_parts.append(f"\nЦелевой канал: {channel_title}")
        if channel_desc:
            user_parts.append(f"Описание канала: {channel_desc[:200]}")
        user_parts.append("Адаптируй текст под тематику канала, если уместно.")

    user_parts.append("\nПерепиши этот текст, сохранив смысл.")

    user_prompt = "\n".join(user_parts)
    return system_prompt, user_prompt
