"""Хендлер модуля «Радар» — поиск каналов и управление подключениями."""

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.radar import (
    get_channel_card_keyboard,
    get_channel_manage_keyboard,
    get_radar_back_keyboard,
    get_radar_menu_keyboard,
    get_user_channels_keyboard,
)
from bot.states.radar import RadarState
from db.repositories.search_profiles import SearchProfileRepository
from services.radar import RadarService

router = Router(name="radar")
logger = logging.getLogger(__name__)

_service = RadarService()
_search_repo = SearchProfileRepository()

# Маппинг назначений для отображения
_PURPOSE_LABELS: dict[str, str] = {
    "broadcast": "Рассылка",
    "vacancies": "Вакансии",
    "both": "Рассылка + Вакансии",
}


async def _cleanup(message: Message, state: FSMContext) -> None:
    """Удаляет предыдущее сообщение бота и сообщение пользователя."""
    data = await state.get_data()
    bot_msg_id = data.get("_bot_msg_id")
    if bot_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, bot_msg_id)
        except Exception:
            pass
    try:
        await message.delete()
    except Exception:
        pass


# ==================== Точка входа ====================

def _has_profile_keywords(user_id: str) -> bool:
    """Проверяет, есть ли у пользователя ключевые слова в профиле."""
    profile = _search_repo.get_active(user_id)
    return bool(profile and profile.get("keywords"))


def _get_profile_keywords(user_id: str) -> list[str]:
    """Возвращает ключевые слова из профиля поиска пользователя."""
    profile = _search_repo.get_active(user_id)
    if profile:
        return profile.get("keywords") or []
    return []


@router.callback_query(F.data == "menu:radar", StateFilter("*"))
async def show_radar(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает меню радара."""
    await state.clear()
    channels = _service.get_user_channels(user["id"])
    count = len(channels)
    text = (
        "<b>Радар</b>\n\n"
        f"Подключено каналов: <b>{count}</b>\n\n"
        "Ищи каналы и чаты с вакансиями по своей нише."
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_radar_menu_keyboard(
            has_channels=count > 0,
            has_profile_keywords=_has_profile_keywords(user["id"]),
        ),
    )
    await callback.answer()


# ==================== Возврат в радар ====================

@router.callback_query(F.data == "rad:back:", StateFilter("*"))
async def back_to_radar(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Возврат в меню радара."""
    await state.clear()
    channels = _service.get_user_channels(user["id"])
    count = len(channels)
    text = (
        "<b>Радар</b>\n\n"
        f"Подключено каналов: <b>{count}</b>\n\n"
        "Ищи каналы и чаты с вакансиями по своей нише."
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_radar_menu_keyboard(
            has_channels=count > 0,
            has_profile_keywords=_has_profile_keywords(user["id"]),
        ),
    )
    await callback.answer()


# ==================== Поиск каналов ====================

@router.callback_query(F.data == "rad:search:", StateFilter("*"))
async def search_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинаем поиск — запрашиваем запрос."""
    await state.set_state(RadarState.searching)
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "<b>Поиск каналов</b>\n\n"
        "Введи запрос для поиска каналов.\n"
        "Например: <i>дизайн фриланс</i>, <i>python разработка</i>",
        reply_markup=get_radar_back_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "rad:profile:", StateFilter("*"))
async def search_by_profile(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Поиск каналов по ключевым словам из профиля."""
    keywords = _get_profile_keywords(user["id"])
    if not keywords:
        await callback.answer("В профиле нет ключевых слов", show_alert=True)
        return

    query = " ".join(keywords)
    await callback.answer()
    await callback.message.edit_text(
        "<b>Поиск каналов</b>\n\n"
        f"Ищу каналы по профилю: <i>{query}</i>..."
    )

    channels = await _service.search_channels(query)

    if not channels:
        await callback.message.edit_text(
            "<b>Поиск каналов</b>\n\n"
            f"По ключевым словам профиля ничего не найдено.\n"
            "Попробуй «Свой запрос» или обнови ключевые слова в профиле.",
            reply_markup=get_radar_back_keyboard(),
        )
        return

    await state.set_state(RadarState.browsing_results)
    await state.update_data(
        search_results=[ch["id"] for ch in channels],
        search_channels=channels,
        current_index=0,
        _bot_msg_id=callback.message.message_id,
    )
    await _show_channel_card(callback.message, channels[0], 0, len(channels))


@router.message(RadarState.searching)
async def search_input(message: Message, user: dict, state: FSMContext) -> None:
    """Выполняем поиск по запросу."""
    query = message.text.strip() if message.text else ""
    if not query:
        await message.answer("Введи поисковый запрос текстом.")
        return

    await _cleanup(message, state)

    # Показываем индикатор загрузки
    loading_msg = await message.answer(
        "<b>Поиск каналов</b>\n\n"
        f"Ищу каналы по запросу: <i>{query}</i>..."
    )

    channels = await _service.search_channels(query)

    if not channels:
        await loading_msg.edit_text(
            "<b>Поиск каналов</b>\n\n"
            f"По запросу «<i>{query}</i>» ничего не найдено.\n"
            "Попробуй другой запрос.",
            reply_markup=get_radar_back_keyboard(),
        )
        await state.clear()
        return

    # Сохраняем результаты в state для пагинации по карточкам
    channel_ids = [ch["id"] for ch in channels]
    await state.set_state(RadarState.browsing_results)
    await state.update_data(
        search_results=channel_ids,
        search_channels=channels,
        current_index=0,
        _bot_msg_id=loading_msg.message_id,
    )

    # Показываем первую карточку
    await _show_channel_card(loading_msg, channels[0], 0, len(channels))


async def _show_channel_card(
    message: Message,
    channel: dict,
    index: int,
    total: int,
) -> None:
    """Показывает карточку канала."""
    title = channel.get("title") or "Без названия"
    username = channel.get("username") or "—"
    description = channel.get("description") or ""
    subs = channel.get("subscribers_count")
    category = channel.get("category") or ""

    subs_text = f"{subs:,}".replace(",", " ") if subs else "—"

    text = (
        f"<b>Канал {index + 1}/{total}</b>\n\n"
        f"<b>{title}</b>\n"
        f"@{username}\n"
    )
    if description:
        # Обрезаем длинное описание
        desc = description[:200] + "..." if len(description) > 200 else description
        text += f"\n{desc}\n"
    text += f"\nПодписчиков: <b>{subs_text}</b>"
    if category:
        text += f"\nКатегория: {category}"
    text += "\n\nВыбери назначение канала:"

    await message.edit_text(
        text,
        reply_markup=get_channel_card_keyboard(channel["id"]),
    )


# ==================== Подключение канала (из карточки) ====================

@router.callback_query(F.data.startswith("rad:link:"), RadarState.browsing_results)
async def link_channel(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Подключает канал с выбранным назначением."""
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Ошибка", show_alert=True)
        return

    channel_id = parts[2]
    purpose = parts[3]

    _service.link_channel(user["id"], channel_id, purpose)
    purpose_label = _PURPOSE_LABELS.get(purpose, purpose)
    await callback.answer(f"Канал подключён: {purpose_label}")

    # Переходим к следующей карточке
    await _next_card(callback, state)


@router.callback_query(F.data == "rad:skip:", RadarState.browsing_results)
async def skip_channel(callback: CallbackQuery, state: FSMContext) -> None:
    """Пропускает текущий канал."""
    await callback.answer()
    await _next_card(callback, state)


async def _next_card(callback: CallbackQuery, state: FSMContext) -> None:
    """Переходит к следующей карточке или завершает просмотр."""
    data = await state.get_data()
    channels = data.get("search_channels", [])
    index = data.get("current_index", 0) + 1

    if index >= len(channels):
        # Все карточки просмотрены
        await state.clear()
        await callback.message.edit_text(
            "<b>Поиск завершён</b>\n\n"
            f"Просмотрено каналов: {len(channels)}",
            reply_markup=get_radar_back_keyboard(),
        )
        return

    await state.update_data(current_index=index)
    await _show_channel_card(callback.message, channels[index], index, len(channels))


# ==================== Список подключённых каналов ====================

@router.callback_query(F.data.startswith("rad:list:"), StateFilter("*"))
async def show_channels_list(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает список подключённых каналов с пагинацией."""
    await state.clear()
    parts = callback.data.split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    channels = _service.get_user_channels(user["id"])
    if not channels:
        await callback.message.edit_text(
            "<b>Мои каналы</b>\n\n"
            "У тебя пока нет подключённых каналов.\n"
            "Используй поиск, чтобы найти каналы по своей нише.",
            reply_markup=get_radar_back_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"<b>Мои каналы</b> ({len(channels)})",
        reply_markup=get_user_channels_keyboard(channels, page=page),
    )
    await callback.answer()


# ==================== Управление каналом ====================

@router.callback_query(F.data.startswith("rad:ch:"), StateFilter("*"))
async def show_channel_details(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает детали подключённого канала."""
    await state.clear()
    parts = callback.data.split(":")
    user_channel_id = parts[2] if len(parts) > 2 else ""

    channels = _service.get_user_channels(user["id"])
    # Ищем нужную связь
    uc = next((c for c in channels if c["id"] == user_channel_id), None)
    if not uc:
        await callback.answer("Канал не найден", show_alert=True)
        return

    ch = uc.get("channels", {})
    title = ch.get("title") or ch.get("username") or "Без названия"
    username = ch.get("username") or "—"
    subs = ch.get("subscribers_count")
    purpose = _PURPOSE_LABELS.get(uc.get("purpose", ""), uc.get("purpose", ""))

    subs_text = f"{subs:,}".replace(",", " ") if subs else "—"

    text = (
        f"<b>{title}</b>\n"
        f"@{username}\n\n"
        f"Подписчиков: <b>{subs_text}</b>\n"
        f"Назначение: <b>{purpose}</b>\n\n"
        "Выбери новое назначение или отключи канал:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_channel_manage_keyboard(user_channel_id, ch.get("id", "")),
    )
    await callback.answer()


# ==================== Изменение назначения ====================

@router.callback_query(F.data.startswith("rad:purpose:"), StateFilter("*"))
async def change_purpose(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Изменяет назначение подключённого канала."""
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Ошибка", show_alert=True)
        return

    user_channel_id = parts[2]
    new_purpose = parts[3]

    _service.update_channel_purpose(user_channel_id, new_purpose)
    purpose_label = _PURPOSE_LABELS.get(new_purpose, new_purpose)
    await callback.answer(f"Назначение изменено: {purpose_label}")

    # Возвращаемся к списку каналов
    channels = _service.get_user_channels(user["id"])
    await callback.message.edit_text(
        f"<b>Мои каналы</b> ({len(channels)})",
        reply_markup=get_user_channels_keyboard(channels, page=0),
    )


# ==================== Отключение канала ====================

@router.callback_query(F.data.startswith("rad:unlink:"), StateFilter("*"))
async def unlink_channel(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Отключает канал от пользователя."""
    parts = callback.data.split(":")
    channel_id = parts[2] if len(parts) > 2 else ""

    _service.unlink_channel(user["id"], channel_id)
    await callback.answer("Канал отключён")

    # Возвращаемся к списку
    channels = _service.get_user_channels(user["id"])
    if not channels:
        await callback.message.edit_text(
            "<b>Мои каналы</b>\n\n"
            "У тебя пока нет подключённых каналов.",
            reply_markup=get_radar_back_keyboard(),
        )
        return

    await callback.message.edit_text(
        f"<b>Мои каналы</b> ({len(channels)})",
        reply_markup=get_user_channels_keyboard(channels, page=0),
    )


# ==================== No-op (пагинация info) ====================

@router.callback_query(F.data == "rad:noop:", StateFilter("*"))
async def noop_handler(callback: CallbackQuery) -> None:
    """Заглушка для информационных кнопок."""
    await callback.answer()
