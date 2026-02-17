"""Хендлер модуля «Мой профиль» — просмотр и редактирование."""

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.onboarding import (
    SPEC_LABELS,
    get_budget_keyboard,
    get_specialization_keyboard,
    get_work_format_keyboard,
)
from bot.keyboards.profile import get_profile_back_keyboard, get_profile_keyboard
from bot.states.profile import ProfileEditState
from db.repositories.search_profiles import SearchProfileRepository
from db.repositories.users import UserRepository

router = Router(name="profile")
logger = logging.getLogger(__name__)

_user_repo = UserRepository()
_search_repo = SearchProfileRepository()

# Маппинг формата работы
_FORMAT_LABELS: dict[str, str] = {
    "oneoff": "Разовые",
    "project": "Проекты",
    "permanent": "Постоянка",
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


def _format_profile_text(user: dict, search_profile: dict | None) -> str:
    """Форматирует текст профиля для отображения."""
    # Специализации
    specs = user.get("specializations") or []
    spec_text = ", ".join(SPEC_LABELS.get(s, s) for s in specs) if specs else "не указаны"

    # Описание услуг
    services = user.get("services_description") or "не указано"

    # Параметры поиска
    if search_profile:
        keywords = search_profile.get("keywords") or []
        kw_text = ", ".join(keywords) if keywords else "не указаны"
        budget = search_profile.get("min_budget")
        budget_text = f"от {budget:,}\u20bd".replace(",", " ") if budget else "любой"
        formats = search_profile.get("work_format") or []
        fmt_text = ", ".join(_FORMAT_LABELS.get(f, f) for f in formats) if formats else "не указан"
    else:
        kw_text = "не указаны"
        budget_text = "любой"
        fmt_text = "не указан"

    return (
        "<b>Мой профиль</b>\n\n"
        f"<b>Специализации:</b> {spec_text}\n"
        f"<b>Описание услуг:</b> {services}\n\n"
        f"<b>Ключевые слова:</b> {kw_text}\n"
        f"<b>Мин. бюджет:</b> {budget_text}\n"
        f"<b>Формат работы:</b> {fmt_text}"
    )


# --- Просмотр профиля ---

@router.callback_query(F.data == "menu:profile", StateFilter("*"))
async def show_profile(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает профиль пользователя."""
    await state.clear()
    search_profile = _search_repo.get_active(user["id"])
    text = _format_profile_text(user, search_profile)
    await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
    await callback.answer()


# --- Возврат в профиль ---

@router.callback_query(F.data == "prof:back:", StateFilter("*"))
async def back_to_profile(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Возврат в профиль после редактирования."""
    await state.clear()
    # Перечитываем пользователя из БД — данные могли измениться
    fresh_user = _user_repo.get_by_telegram_id(user["telegram_id"])
    if fresh_user is None:
        fresh_user = user
    search_profile = _search_repo.get_active(fresh_user["id"])
    text = _format_profile_text(fresh_user, search_profile)
    await callback.message.edit_text(text, reply_markup=get_profile_keyboard())
    await callback.answer()


# ==================== Редактирование специализаций ====================

@router.callback_query(F.data == "prof:edit:specializations", StateFilter("*"))
async def edit_specializations_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Начинаем редактирование специализаций."""
    current = user.get("specializations") or []
    await state.set_state(ProfileEditState.editing_specializations)
    await state.update_data(
        specializations=list(current),
        _user_id=user["id"],
        _bot_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        "<b>Редактирование специализаций</b>\n\n"
        "Выбери специализации и нажми «Далее».",
        reply_markup=get_specialization_keyboard(list(current)),
    )
    await callback.answer()


@router.callback_query(
    ProfileEditState.editing_specializations,
    F.data.startswith("onb:spec:"),
)
async def edit_specializations_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    """Переключение специализации при редактировании."""
    parts = callback.data.split(":")
    value = parts[2] if len(parts) > 2 else ""

    data = await state.get_data()
    selected: list[str] = data.get("specializations", [])

    if value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы одну специализацию!", show_alert=True)
            return
        user_id = data.get("_user_id") or ""
        if not user_id:
            await callback.answer("Ошибка. Попробуй ещё раз.", show_alert=True)
            return
        _user_repo.update(user_id, specializations=selected)
        await state.clear()
        fresh_user = _user_repo.get_by_telegram_id(callback.from_user.id)
        search_profile = _search_repo.get_active(user_id)
        text = _format_profile_text(fresh_user, search_profile)
        await callback.message.edit_text(
            text + "\n\n\u2705 Специализации обновлены!",
            reply_markup=get_profile_keyboard(),
        )
        await callback.answer()
        return

    if value == "custom":
        await state.set_state(ProfileEditState.editing_specialization_custom)
        await callback.message.edit_text(
            "<b>Своя специализация</b>\n\n"
            "Напиши название своей специализации.",
        )
        await state.update_data(_bot_msg_id=callback.message.message_id)
        await callback.answer()
        return

    # Переключаем
    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)

    await state.update_data(specializations=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_specialization_keyboard(selected),
    )
    await callback.answer()


@router.callback_query(
    ProfileEditState.editing_specializations,
    F.data.startswith("onb:spec_del:"),
)
async def edit_specializations_delete(callback: CallbackQuery, state: FSMContext) -> None:
    """Удаление пользовательской специализации при редактировании."""
    parts = callback.data.split(":")
    idx = int(parts[2]) if len(parts) > 2 else -1
    data = await state.get_data()
    selected: list[str] = data.get("specializations", [])
    if 0 <= idx < len(selected):
        selected.pop(idx)
    await state.update_data(specializations=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_specialization_keyboard(selected),
    )
    await callback.answer()


@router.message(ProfileEditState.editing_specialization_custom)
async def edit_specialization_custom_input(message: Message, state: FSMContext) -> None:
    """Добавляем пользовательскую специализацию → возврат к мультивыбору."""
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("Напиши название специализации текстом.")
        return

    await _cleanup(message, state)

    data = await state.get_data()
    selected: list[str] = data.get("specializations", [])
    if text not in selected:
        selected.append(text)
    await state.update_data(specializations=selected)

    await state.set_state(ProfileEditState.editing_specializations)
    sent = await message.answer(
        f"<b>Редактирование специализаций</b>\n\n"
        f"Добавлено: <b>{text}</b>\nМожешь выбрать ещё или нажми «Далее».",
        reply_markup=get_specialization_keyboard(selected),
    )
    await state.update_data(_bot_msg_id=sent.message_id)


# ==================== Редактирование описания услуг ====================

@router.callback_query(F.data == "prof:edit:services", StateFilter("*"))
async def edit_services_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начинаем редактирование описания услуг."""
    await state.set_state(ProfileEditState.editing_services)
    await callback.message.edit_text(
        "<b>Редактирование описания услуг</b>\n\n"
        "Напиши новое описание услуг.\n"
        "Например: <i>Делаю Telegram-ботов, автоматизирую бизнес-процессы</i>",
        reply_markup=get_profile_back_keyboard(),
    )
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.answer()


@router.message(ProfileEditState.editing_services)
async def edit_services_input(message: Message, user: dict, state: FSMContext) -> None:
    """Сохраняем новое описание услуг."""
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("Напиши описание услуг текстом.")
        return

    await _cleanup(message, state)

    _user_repo.update(user["id"], services_description=text)
    await state.clear()

    fresh_user = _user_repo.get_by_telegram_id(user["telegram_id"])
    search_profile = _search_repo.get_active(user["id"])
    text_profile = _format_profile_text(fresh_user, search_profile)
    await message.answer(
        text_profile + "\n\n\u2705 Описание обновлено!",
        reply_markup=get_profile_keyboard(),
    )


# ==================== Редактирование параметров поиска ====================

@router.callback_query(F.data == "prof:edit:search", StateFilter("*"))
async def edit_search_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Начинаем редактирование параметров поиска — ключевые слова."""
    search_profile = _search_repo.get_active(user["id"])
    profile_id = search_profile["id"] if search_profile else None
    await state.set_state(ProfileEditState.editing_keywords)
    await state.update_data(
        search_profile_id=profile_id,
        _bot_msg_id=callback.message.message_id,
    )
    current_kw = ", ".join(search_profile.get("keywords", [])) if search_profile else ""
    hint = f"\nТекущие: <i>{current_kw}</i>" if current_kw else ""
    await callback.message.edit_text(
        "<b>Параметры поиска — Ключевые слова</b>\n\n"
        f"Введи ключевые слова через запятую.{hint}",
        reply_markup=get_profile_back_keyboard(),
    )
    await callback.answer()


@router.message(ProfileEditState.editing_keywords)
async def edit_keywords_input(message: Message, user: dict, state: FSMContext) -> None:
    """Сохраняем ключевые слова → бюджет."""
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("Введи ключевые слова через запятую.")
        return

    await _cleanup(message, state)

    keywords = [kw.strip() for kw in text.split(",") if kw.strip()]
    await state.update_data(keywords=keywords)
    await state.set_state(ProfileEditState.editing_budget)
    sent = await message.answer(
        "<b>Параметры поиска — Минимальный бюджет</b>\n\n"
        "Какой минимальный бюджет проекта тебя интересует?",
        reply_markup=get_budget_keyboard(),
    )
    await state.update_data(_bot_msg_id=sent.message_id)


@router.callback_query(
    ProfileEditState.editing_budget,
    F.data.startswith("onb:budget:"),
)
async def edit_budget_input(callback: CallbackQuery, state: FSMContext) -> None:
    """Сохраняем бюджет → формат работы."""
    parts = callback.data.split(":")
    budget = int(parts[2]) if len(parts) > 2 else 0
    await state.update_data(min_budget=budget if budget > 0 else None, work_formats=[])
    await state.set_state(ProfileEditState.editing_format)
    await callback.message.edit_text(
        "<b>Параметры поиска — Формат работы</b>\n\n"
        "Какой формат работы тебе подходит? Выбери и нажми «Далее».",
        reply_markup=get_work_format_keyboard(),
    )
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(
    ProfileEditState.editing_format,
    F.data.startswith("onb:format:"),
)
async def edit_format_toggle(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Переключение формата работы → сохранение при «Далее»."""
    parts = callback.data.split(":")
    value = parts[2] if len(parts) > 2 else ""

    data = await state.get_data()
    selected: list[str] = data.get("work_formats", [])

    if value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы один формат!", show_alert=True)
            return
        # Сохраняем все параметры поиска
        profile_id = data.get("search_profile_id")
        keywords = data.get("keywords", [])
        min_budget = data.get("min_budget")

        if profile_id:
            _search_repo.update(
                profile_id,
                keywords=keywords,
                min_budget=min_budget,
                work_format=selected,
            )
        else:
            _search_repo.create(
                user_id=user["id"],
                keywords=keywords,
                min_budget=min_budget,
                work_format=selected,
            )

        await state.clear()
        fresh_user = _user_repo.get_by_telegram_id(user["telegram_id"])
        search_profile = _search_repo.get_active(user["id"])
        text = _format_profile_text(fresh_user, search_profile)
        await callback.message.edit_text(
            text + "\n\n\u2705 Параметры поиска обновлены!",
            reply_markup=get_profile_keyboard(),
        )
        await callback.answer()
        return

    # Переключаем
    if value in selected:
        selected.remove(value)
    else:
        selected.append(value)

    await state.update_data(work_formats=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_work_format_keyboard(selected),
    )
    await callback.answer()
