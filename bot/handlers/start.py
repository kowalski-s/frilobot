"""Хендлер /start, приветствие и онбординг."""

import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.menu import get_main_menu_keyboard
from bot.keyboards.onboarding import (
    OnboardingCallback,
    get_budget_keyboard,
    get_disclaimer_keyboard,
    get_specialization_keyboard,
    get_welcome_keyboard,
    get_work_format_keyboard,
)
from bot.states.onboarding import OnboardingState
from db.repositories.search_profiles import SearchProfileRepository
from db.repositories.users import UserRepository

router = Router(name="start")
logger = logging.getLogger(__name__)

_user_repo = UserRepository()
_search_repo = SearchProfileRepository()


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


# --- /start ---

@router.message(CommandStart())
async def cmd_start(message: Message, user: dict, state: FSMContext) -> None:
    """Обработка команды /start."""
    # Сбрасываем FSM на случай повторного /start
    await state.clear()

    name = user.get("first_name") or message.from_user.first_name or "друг"

    if user.get("onboarding_completed"):
        sent = await message.answer(
            f"Привет, {name}! Что делаем?",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    # Онбординг: шаг 1 — приветствие
    await state.set_state(OnboardingState.welcome)
    sent = await message.answer(
        f"Привет, {name}! Я — <b>Frilo</b>, помощник фрилансера.\n\n"
        "Помогу найти каналы по твоей нише, составить продающее сообщение "
        "и разослать его с безопасной частотой.\n\n"
        "Давай настроим профиль — это займёт пару минут.",
        reply_markup=get_welcome_keyboard(),
    )
    await state.update_data(_bot_msg_id=sent.message_id)


# --- Шаг 1 → 2: welcome → specialization ---

@router.callback_query(
    OnboardingState.welcome,
    OnboardingCallback.filter(F.step == "welcome"),
)
async def onb_welcome(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать настройку → выбор специализаций."""
    await state.update_data(specializations=[])
    await state.set_state(OnboardingState.specialization)
    await callback.message.edit_text(
        "<b>Шаг 1/6 — Специализация</b>\n\n"
        "Выбери одну или несколько специализаций, затем нажми «Далее».",
        reply_markup=get_specialization_keyboard(),
    )
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.answer()


# --- Шаг 2: specialization (мультивыбор) ---

@router.callback_query(
    OnboardingState.specialization,
    OnboardingCallback.filter(F.step == "spec"),
)
async def onb_specialization(
    callback: CallbackQuery, callback_data: OnboardingCallback, state: FSMContext,
) -> None:
    """Переключение специализаций или переход дальше."""
    data = await state.get_data()
    selected: list[str] = data.get("specializations", [])

    if callback_data.value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы одну специализацию!", show_alert=True)
            return
        # Переход к шагу 3
        await state.set_state(OnboardingState.services)
        await callback.message.edit_text(
            "<b>Шаг 2/6 — Описание услуг</b>\n\n"
            "Напиши коротко, какие услуги ты предлагаешь.\n"
            "Например: <i>Делаю Telegram-ботов, автоматизирую бизнес-процессы</i>",
        )
        await state.update_data(_bot_msg_id=callback.message.message_id)
        await callback.answer()
        return

    if callback_data.value == "custom":
        # Переход к вводу своей специализации
        await state.set_state(OnboardingState.specialization_custom)
        await callback.message.edit_text(
            "<b>Шаг 1/6 — Своя специализация</b>\n\n"
            "Напиши название своей специализации.\n"
            "Например: <i>3D-моделирование</i>, <i>Видеомонтаж</i>, <i>Аналитика данных</i>",
        )
        await state.update_data(_bot_msg_id=callback.message.message_id)
        await callback.answer()
        return

    # Переключаем выбор предустановленной
    if callback_data.value in selected:
        selected.remove(callback_data.value)
    else:
        selected.append(callback_data.value)

    await state.update_data(specializations=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_specialization_keyboard(selected),
    )
    await callback.answer()


# --- Шаг 2: удаление пользовательской специализации ---

@router.callback_query(
    OnboardingState.specialization,
    OnboardingCallback.filter(F.step == "spec_del"),
)
async def onb_spec_delete(
    callback: CallbackQuery, callback_data: OnboardingCallback, state: FSMContext,
) -> None:
    """Удаляем пользовательскую специализацию по индексу."""
    data = await state.get_data()
    selected: list[str] = data.get("specializations", [])
    idx = int(callback_data.value)
    if 0 <= idx < len(selected):
        selected.pop(idx)
    await state.update_data(specializations=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_specialization_keyboard(selected),
    )
    await callback.answer()


# --- Шаг 2а: specialization_custom (ввод своей специализации) ---

@router.message(OnboardingState.specialization_custom)
async def onb_specialization_custom(message: Message, state: FSMContext) -> None:
    """Добавляем пользовательскую специализацию → возврат к выбору."""
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

    await state.set_state(OnboardingState.specialization)
    sent = await message.answer(
        "<b>Шаг 1/6 — Специализация</b>\n\n"
        f"Добавлено: <b>{text}</b>\n"
        "Можешь выбрать ещё или нажми «Далее».",
        reply_markup=get_specialization_keyboard(selected),
    )
    await state.update_data(_bot_msg_id=sent.message_id)


# --- Шаг 3: services (ввод текстом) ---

@router.message(OnboardingState.services)
async def onb_services(message: Message, state: FSMContext) -> None:
    """Сохраняем описание услуг → переход к ключевым словам."""
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("Напиши описание услуг текстом.")
        return

    await _cleanup(message, state)

    await state.update_data(services_description=text)
    await state.set_state(OnboardingState.search_keywords)
    sent = await message.answer(
        "<b>Шаг 3/6 — Ключевые слова</b>\n\n"
        "Введи ключевые слова для поиска заказов через запятую.\n"
        "Например: <i>python, бот, telegram, автоматизация</i>",
    )
    await state.update_data(_bot_msg_id=sent.message_id)


# --- Шаг 4: search_keywords (ввод текстом) ---

@router.message(OnboardingState.search_keywords)
async def onb_keywords(message: Message, state: FSMContext) -> None:
    """Сохраняем ключевые слова → выбор бюджета."""
    text = message.text.strip() if message.text else ""
    if not text:
        await message.answer("Введи ключевые слова через запятую.")
        return

    await _cleanup(message, state)

    keywords = [kw.strip() for kw in text.split(",") if kw.strip()]
    await state.update_data(keywords=keywords)
    await state.set_state(OnboardingState.search_budget)
    sent = await message.answer(
        "<b>Шаг 4/6 — Минимальный бюджет</b>\n\n"
        "Какой минимальный бюджет проекта тебя интересует?",
        reply_markup=get_budget_keyboard(),
    )
    await state.update_data(_bot_msg_id=sent.message_id)


# --- Шаг 5: search_budget ---

@router.callback_query(
    OnboardingState.search_budget,
    OnboardingCallback.filter(F.step == "budget"),
)
async def onb_budget(
    callback: CallbackQuery, callback_data: OnboardingCallback, state: FSMContext,
) -> None:
    """Сохраняем бюджет → выбор формата работы."""
    budget = int(callback_data.value)
    await state.update_data(min_budget=budget if budget > 0 else None)
    await state.update_data(work_formats=[])
    await state.set_state(OnboardingState.search_format)
    await callback.message.edit_text(
        "<b>Шаг 5/6 — Формат работы</b>\n\n"
        "Какой формат работы тебе подходит? Выбери один или несколько, затем «Далее».",
        reply_markup=get_work_format_keyboard(),
    )
    await state.update_data(_bot_msg_id=callback.message.message_id)
    await callback.answer()


# --- Шаг 6: search_format (мультивыбор) ---

@router.callback_query(
    OnboardingState.search_format,
    OnboardingCallback.filter(F.step == "format"),
)
async def onb_format(
    callback: CallbackQuery, callback_data: OnboardingCallback, state: FSMContext,
) -> None:
    """Переключение форматов работы или переход к дисклеймеру."""
    data = await state.get_data()
    selected: list[str] = data.get("work_formats", [])

    if callback_data.value == "done":
        if not selected:
            await callback.answer("Выбери хотя бы один формат!", show_alert=True)
            return
        # Переход к дисклеймеру
        await state.set_state(OnboardingState.disclaimer)
        await callback.message.edit_text(
            "<b>Шаг 6/6 — Дисклеймер</b>\n\n"
            "Frilo может рассылать сообщения в каналы от твоего имени. "
            "Это несёт риски: Telegram может ограничить аккаунт за спам.\n\n"
            "Ты понимаешь и принимаешь эти риски?",
            reply_markup=get_disclaimer_keyboard(),
        )
        await callback.answer()
        return

    # Переключаем выбор
    if callback_data.value in selected:
        selected.remove(callback_data.value)
    else:
        selected.append(callback_data.value)

    await state.update_data(work_formats=selected)
    await callback.message.edit_reply_markup(
        reply_markup=get_work_format_keyboard(selected),
    )
    await callback.answer()


# --- Шаг 7: disclaimer → финал ---

@router.callback_query(
    OnboardingState.disclaimer,
    OnboardingCallback.filter(F.step == "disclaimer"),
)
async def onb_disclaimer(
    callback: CallbackQuery,
    callback_data: OnboardingCallback,
    state: FSMContext,
    user: dict,
) -> None:
    """Принятие/отклонение рисков → сохранение данных → главное меню."""
    data = await state.get_data()
    user_id: str = user["id"]

    disclaimer_accepted = callback_data.value == "accept"

    # Сохраняем профиль пользователя
    _user_repo.update(
        user_id,
        specializations=data.get("specializations", []),
        services_description=data.get("services_description", ""),
        disclaimer_accepted=disclaimer_accepted,
    )
    _user_repo.complete_onboarding(user_id)

    # Создаём профиль поиска
    _search_repo.create(
        user_id=user_id,
        keywords=data.get("keywords", []),
        min_budget=data.get("min_budget"),
        work_format=data.get("work_formats", []),
    )

    logger.info("Onboarding completed: user_id=%s", user_id)
    await state.clear()

    name = user.get("first_name") or "друг"
    status = "Отлично" if disclaimer_accepted else "Понял"
    await callback.message.edit_text(
        f"{status}, {name}! Профиль настроен. Что делаем?",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()
