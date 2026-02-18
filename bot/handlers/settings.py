"""Хендлер модуля «Настройки» — просмотр и изменение."""

import logging
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.settings import (
    get_limit_keyboard,
    get_settings_back_keyboard,
    get_settings_keyboard,
)
from bot.states.settings import SettingsEditState
from db.repositories.settings import SettingsRepository

router = Router(name="settings")
logger = logging.getLogger(__name__)

_settings_repo = SettingsRepository()

# Паттерн для времени ЧЧ:ММ
_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")

# Паттерн для задержек: два числа через дефис или пробел
_DELAYS_RE = re.compile(r"^(\d+)\s*[-–—\s]\s*(\d+)$")


def _format_settings_text(settings: dict) -> str:
    """Форматирует текст настроек для отображения."""
    limit = settings.get("broadcast_limit_per_hour", 5)
    quiet_start = settings.get("quiet_hours_start", "23:00:00")
    quiet_end = settings.get("quiet_hours_end", "08:00:00")
    min_delay = settings.get("min_delay_seconds", 30)
    max_delay = settings.get("max_delay_seconds", 120)

    # Обрезаем секунды из времени (23:00:00 → 23:00)
    quiet_start = str(quiet_start)[:5]
    quiet_end = str(quiet_end)[:5]

    return (
        "<b>Настройки</b>\n\n"
        f"<b>Лимит рассылки:</b> {limit} сообщений/час\n"
        f"<b>Тихие часы:</b> {quiet_start} — {quiet_end}\n"
        f"<b>Задержки:</b> {min_delay}–{max_delay} сек"
    )


def _parse_time(text: str) -> tuple[int, int] | None:
    """Парсит время в формате ЧЧ:ММ. Возвращает (часы, минуты) или None."""
    m = _TIME_RE.match(text.strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mi <= 59:
        return (h, mi)
    return None


# --- Просмотр настроек ---

@router.callback_query(F.data == "menu:settings", StateFilter("*"))
async def show_settings(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает настройки пользователя."""
    await state.clear()
    settings = _settings_repo.get_by_user_id(user["id"])
    if not settings:
        settings = _settings_repo.create_default(user["id"])
    text = _format_settings_text(settings)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback.answer()


# --- Возврат в настройки ---

@router.callback_query(F.data == "sett:back:", StateFilter("*"))
async def back_to_settings(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Возврат в настройки."""
    await state.clear()
    settings = _settings_repo.get_by_user_id(user["id"])
    if not settings:
        settings = _settings_repo.create_default(user["id"])
    text = _format_settings_text(settings)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback.answer()


# ==================== Лимит рассылки ====================

@router.callback_query(F.data == "sett:edit:limit", StateFilter("*"))
async def edit_limit_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Начинаем редактирование лимита рассылки."""
    await state.clear()
    settings = _settings_repo.get_by_user_id(user["id"])
    current = settings.get("broadcast_limit_per_hour", 5) if settings else 5
    await callback.message.edit_text(
        "<b>Лимит рассылки</b>\n\n"
        "Сколько сообщений в час отправлять?\n"
        "Чем меньше — тем безопаснее для аккаунта.",
        reply_markup=get_limit_keyboard(current),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sett:limit:"), StateFilter("*"))
async def edit_limit_select(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Сохраняем выбранный лимит."""
    parts = callback.data.split(":")
    try:
        new_limit = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("Ошибка", show_alert=True)
        return

    _settings_repo.update(user["id"], broadcast_limit_per_hour=new_limit)
    settings = _settings_repo.get_by_user_id(user["id"])
    text = _format_settings_text(settings)
    await callback.message.edit_text(
        text + "\n\n\u2705 Лимит обновлён!",
        reply_markup=get_settings_keyboard(),
    )
    await callback.answer()


# ==================== Тихие часы ====================

@router.callback_query(F.data == "sett:edit:quiet", StateFilter("*"))
async def edit_quiet_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Начинаем редактирование тихих часов."""
    settings = _settings_repo.get_by_user_id(user["id"])
    quiet_start = str(settings.get("quiet_hours_start", "23:00:00"))[:5] if settings else "23:00"
    quiet_end = str(settings.get("quiet_hours_end", "08:00:00"))[:5] if settings else "08:00"

    await state.set_state(SettingsEditState.editing_quiet_hours)
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "<b>Тихие часы</b>\n\n"
        f"Текущие: <b>{quiet_start} — {quiet_end}</b>\n\n"
        "Введи новый диапазон в формате:\n"
        "<code>23:00-08:00</code>",
        reply_markup=get_settings_back_keyboard(),
    )
    await callback.answer()


@router.message(SettingsEditState.editing_quiet_hours)
async def edit_quiet_input(message: Message, user: dict, state: FSMContext) -> None:
    """Сохраняем тихие часы."""
    text = message.text.strip() if message.text else ""

    # Парсим формат "ЧЧ:ММ-ЧЧ:ММ" или "ЧЧ:ММ ЧЧ:ММ"
    parts = re.split(r"\s*[-–—]\s*", text, maxsplit=1)
    if len(parts) != 2:
        await message.answer(
            "Неверный формат. Введи в формате <code>23:00-08:00</code>.",
        )
        return

    start_parsed = _parse_time(parts[0])
    end_parsed = _parse_time(parts[1])

    if not start_parsed or not end_parsed:
        await message.answer(
            "Неверное время. Введи в формате <code>23:00-08:00</code>.",
        )
        return

    # Очистка предыдущих сообщений
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

    quiet_start = f"{start_parsed[0]:02d}:{start_parsed[1]:02d}"
    quiet_end = f"{end_parsed[0]:02d}:{end_parsed[1]:02d}"

    _settings_repo.update(
        user["id"],
        quiet_hours_start=quiet_start,
        quiet_hours_end=quiet_end,
    )
    await state.clear()

    settings = _settings_repo.get_by_user_id(user["id"])
    text_settings = _format_settings_text(settings)
    await message.answer(
        text_settings + "\n\n\u2705 Тихие часы обновлены!",
        reply_markup=get_settings_keyboard(),
    )


# ==================== Задержки ====================

@router.callback_query(F.data == "sett:edit:delays", StateFilter("*"))
async def edit_delays_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Начинаем редактирование задержек между сообщениями."""
    settings = _settings_repo.get_by_user_id(user["id"])
    min_d = settings.get("min_delay_seconds", 30) if settings else 30
    max_d = settings.get("max_delay_seconds", 120) if settings else 120

    await state.set_state(SettingsEditState.editing_delays)
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.message.edit_text(
        "<b>Задержки между сообщениями</b>\n\n"
        f"Текущие: <b>{min_d}–{max_d} сек</b>\n\n"
        "Введи минимальную и максимальную задержку в секундах:\n"
        "<code>30-120</code>",
        reply_markup=get_settings_back_keyboard(),
    )
    await callback.answer()


@router.message(SettingsEditState.editing_delays)
async def edit_delays_input(message: Message, user: dict, state: FSMContext) -> None:
    """Сохраняем задержки."""
    text = message.text.strip() if message.text else ""

    m = _DELAYS_RE.match(text)
    if not m:
        await message.answer(
            "Неверный формат. Введи в формате <code>30-120</code> (секунды).",
        )
        return

    min_delay = int(m.group(1))
    max_delay = int(m.group(2))

    if min_delay < 5:
        await message.answer("Минимальная задержка — 5 секунд.")
        return
    if max_delay < min_delay:
        await message.answer("Максимальная задержка должна быть больше минимальной.")
        return
    if max_delay > 600:
        await message.answer("Максимальная задержка — 600 секунд (10 минут).")
        return

    # Очистка предыдущих сообщений
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

    _settings_repo.update(
        user["id"],
        min_delay_seconds=min_delay,
        max_delay_seconds=max_delay,
    )
    await state.clear()

    settings = _settings_repo.get_by_user_id(user["id"])
    text_settings = _format_settings_text(settings)
    await message.answer(
        text_settings + "\n\n\u2705 Задержки обновлены!",
        reply_markup=get_settings_keyboard(),
    )
