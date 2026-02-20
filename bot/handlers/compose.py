"""Хендлер модуля «Составить текст» — чат-формат с ИИ."""

import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.compose import (
    get_broadcast_chat_keyboard,
    get_compose_back_keyboard,
    get_compose_menu_keyboard,
    get_result_keyboard,
    get_template_detail_keyboard,
    get_templates_keyboard,
    get_vacancy_chat_keyboard,
)
from bot.states.compose import ComposeState
from services.composer import ComposerService

router = Router(name="compose")
logger = logging.getLogger(__name__)

_service = ComposerService()


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

@router.callback_query(F.data == "menu:compose", StateFilter("*"))
async def show_compose_menu(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает меню модуля «Составить текст»."""
    await state.clear()
    templates = _service.get_templates(user["id"])
    await callback.message.edit_text(
        "<b>Составить текст</b>\n\n"
        "Генерирую продающие сообщения и отклики на вакансии с помощью ИИ.\n"
        "Расскажи, что нужно — я помогу составить текст.",
        reply_markup=get_compose_menu_keyboard(has_templates=len(templates) > 0),
    )
    await callback.answer()


# ==================== Возврат ====================

@router.callback_query(F.data == "cmp:back:", StateFilter("*"))
async def back_to_compose(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Возврат в меню составления текста."""
    await state.clear()
    templates = _service.get_templates(user["id"])
    await callback.message.edit_text(
        "<b>Составить текст</b>\n\n"
        "Генерирую продающие сообщения и отклики на вакансии с помощью ИИ.\n"
        "Расскажи, что нужно — я помогу составить текст.",
        reply_markup=get_compose_menu_keyboard(has_templates=len(templates) > 0),
    )
    await callback.answer()


# ==================== Рассылочное сообщение — начало чата ====================

@router.callback_query(F.data == "cmp:broadcast:", StateFilter("*"))
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Начало чат-режима для рассылочного сообщения."""
    await state.clear()
    await state.set_state(ComposeState.collecting_broadcast_info)
    await state.update_data(
        chat_history=[],
        msg_type="broadcast",
        length="medium",
        last_result=None,
        _bot_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        "<b>Сообщение для рассылки</b>\n\n"
        "Расскажи, что хочешь предложить. Какие услуги, для кого, "
        "что важно подчеркнуть?\n\n"
        "Или нажми «Сгенерировать по профилю» — я составлю сообщение "
        "из данных твоего профиля.\n\n"
        "Выбери длину сообщения кнопками ниже.",
        reply_markup=get_broadcast_chat_keyboard(),
    )
    await callback.answer()


# ==================== Выбор длины ====================

@router.callback_query(
    F.data.startswith("cmp:len:"),
    ComposeState.collecting_broadcast_info,
)
async def set_length(callback: CallbackQuery, state: FSMContext) -> None:
    """Устанавливает длину сообщения."""
    length = callback.data.split(":")[2]
    if length not in ("short", "medium", "long"):
        length = "medium"
    await state.update_data(length=length)
    labels = {"short": "Короткое", "medium": "Среднее", "long": "Длинное"}
    await callback.answer(f"Длина: {labels[length]}")


# ==================== Генерация по профилю ====================

@router.callback_query(
    F.data == "cmp:from_profile:",
    ComposeState.collecting_broadcast_info,
)
async def generate_from_profile(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Генерирует рассылку сразу из данных профиля."""
    data = await state.get_data()
    length = data.get("length", "medium")

    await callback.message.edit_text(
        "<b>Сообщение для рассылки</b>\n\n"
        "Генерирую на основе профиля..."
    )
    await callback.answer()

    try:
        result, chat_history = await _service.generate_broadcast_from_profile(
            user_id=user["id"],
            length=length,
        )
    except Exception as e:
        logger.exception("Failed to generate from profile")
        await callback.message.edit_text(
            f"<b>Ошибка генерации</b>\n\n{e}\nПопробуй позже.",
            reply_markup=get_compose_back_keyboard(),
        )
        await state.clear()
        return

    await state.set_state(ComposeState.refining)
    await state.update_data(
        chat_history=chat_history,
        last_result=result,
        msg_type="broadcast",
        length=length,
        _bot_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        f"<b>Результат</b>\n\n{result}",
        reply_markup=get_result_keyboard(),
    )


# ==================== Текстовый ввод — сбор инфо для рассылки ====================

@router.message(ComposeState.collecting_broadcast_info)
async def broadcast_text_input(message: Message, user: dict, state: FSMContext) -> None:
    """Пользователь пишет текстом — добавляем в историю, генерируем."""
    text = message.text.strip() if message.text else ""
    if not text:
        return

    await _cleanup(message, state)
    data = await state.get_data()
    chat_history: list[dict] = data.get("chat_history", [])
    length = data.get("length", "medium")

    # Добавляем сообщение пользователя
    chat_history.append({"role": "user", "content": text})

    loading_msg = await message.answer(
        "<b>Сообщение для рассылки</b>\n\n"
        "Генерирую..."
    )

    try:
        result = await _service.generate_broadcast(
            user_id=user["id"],
            chat_history=chat_history,
            length=length,
        )
    except Exception as e:
        logger.exception("Failed to generate broadcast")
        await loading_msg.edit_text(
            f"<b>Ошибка генерации</b>\n\n{e}\nПопробуй позже.",
            reply_markup=get_compose_back_keyboard(),
        )
        await state.clear()
        return

    chat_history.append({"role": "assistant", "content": result})

    await state.set_state(ComposeState.refining)
    await state.update_data(
        chat_history=chat_history,
        last_result=result,
        _bot_msg_id=loading_msg.message_id,
    )
    await loading_msg.edit_text(
        f"<b>Результат</b>\n\n{result}",
        reply_markup=get_result_keyboard(),
    )


# ==================== Отклик на вакансию — начало ====================

@router.callback_query(F.data == "cmp:vacancy:", StateFilter("*"))
async def vacancy_start(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Начало чат-режима для отклика на вакансию."""
    await state.clear()

    try:
        chat_history = await _service.init_vacancy_chat(user["id"])
    except Exception as e:
        logger.exception("Failed to init vacancy chat")
        await callback.message.edit_text(
            f"<b>Ошибка</b>\n\n{e}",
            reply_markup=get_compose_back_keyboard(),
        )
        await callback.answer()
        return

    await state.set_state(ComposeState.collecting_vacancy_info)
    await state.update_data(
        chat_history=chat_history,
        msg_type="vacancy",
        last_result=None,
        has_vacancy=False,
        _bot_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        "<b>Отклик на вакансию</b>\n\n"
        "Вставь текст вакансии.\n"
        "Также можешь добавить резюме или дополнительную информацию о себе.",
        reply_markup=get_vacancy_chat_keyboard(can_generate=False),
    )
    await callback.answer()


# ==================== Текстовый ввод — вакансия ====================

@router.message(ComposeState.collecting_vacancy_info)
async def vacancy_text_input(message: Message, user: dict, state: FSMContext) -> None:
    """Пользователь вставляет вакансию / резюме / доп. информацию."""
    text = message.text.strip() if message.text else ""
    if not text:
        return

    await _cleanup(message, state)
    data = await state.get_data()
    chat_history: list[dict] = data.get("chat_history", [])
    has_vacancy = data.get("has_vacancy", False)

    # Добавляем сообщение пользователя
    chat_history.append({"role": "user", "content": text})

    if not has_vacancy:
        # Первое сообщение — вакансия
        bot_msg = await message.answer(
            "<b>Отклик на вакансию</b>\n\n"
            "Получил вакансию. Хочешь добавить резюме или дополнительную "
            "информацию? Или нажми «Сгенерировать».",
            reply_markup=get_vacancy_chat_keyboard(can_generate=True),
        )
        await state.update_data(
            chat_history=chat_history,
            has_vacancy=True,
            _bot_msg_id=bot_msg.message_id,
        )
    else:
        # Дополнительная информация — показываем кнопку генерации
        bot_msg = await message.answer(
            "<b>Отклик на вакансию</b>\n\n"
            "Принял. Можешь добавить ещё или нажми «Сгенерировать».",
            reply_markup=get_vacancy_chat_keyboard(can_generate=True),
        )
        await state.update_data(
            chat_history=chat_history,
            _bot_msg_id=bot_msg.message_id,
        )


# ==================== Генерация отклика ====================

@router.callback_query(
    F.data == "cmp:gen_vacancy:",
    ComposeState.collecting_vacancy_info,
)
async def generate_vacancy(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Генерирует отклик на вакансию из собранной информации."""
    data = await state.get_data()
    chat_history: list[dict] = data.get("chat_history", [])

    # Добавляем инструкцию генерации
    chat_history.append({"role": "user", "content": "Напиши отклик на эту вакансию от моего лица."})

    await callback.message.edit_text(
        "<b>Отклик на вакансию</b>\n\n"
        "Генерирую отклик..."
    )
    await callback.answer()

    try:
        result = await _service.generate_vacancy_response(
            user_id=user["id"],
            chat_history=chat_history,
        )
    except Exception as e:
        logger.exception("Failed to generate vacancy response")
        await callback.message.edit_text(
            f"<b>Ошибка генерации</b>\n\n{e}\nПопробуй позже.",
            reply_markup=get_compose_back_keyboard(),
        )
        await state.clear()
        return

    chat_history.append({"role": "assistant", "content": result})

    await state.set_state(ComposeState.refining)
    await state.update_data(
        chat_history=chat_history,
        last_result=result,
        _bot_msg_id=callback.message.message_id,
    )
    await callback.message.edit_text(
        f"<b>Результат</b>\n\n{result}",
        reply_markup=get_result_keyboard(),
    )


# ==================== Панель действий: сохранить ====================

@router.callback_query(F.data == "cmp:save:", ComposeState.refining)
async def save_result(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Сохраняет результат как шаблон."""
    data = await state.get_data()
    last_result = data.get("last_result", "")
    msg_type = data.get("msg_type", "broadcast")

    if not last_result:
        await callback.answer("Нечего сохранять", show_alert=True)
        return

    _service.save_as_template(user["id"], last_result, msg_type=msg_type)
    await callback.answer("Сохранено как шаблон!")


# ==================== Панель действий: переделать ====================

@router.callback_query(F.data == "cmp:regen:", ComposeState.refining)
async def regenerate(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Полная перегенерация — удаляет последний ответ из истории."""
    data = await state.get_data()
    chat_history: list[dict] = data.get("chat_history", [])
    msg_type = data.get("msg_type", "broadcast")
    length = data.get("length", "medium")

    # Убираем последний ответ ассистента
    if chat_history and chat_history[-1]["role"] == "assistant":
        chat_history.pop()

    await callback.message.edit_text(
        "<b>Переделываю...</b>"
    )
    await callback.answer()

    try:
        result = await _service.refine(
            user_id=user["id"],
            chat_history=chat_history,
            msg_type=msg_type,
            length=length,
        )
    except Exception as e:
        logger.exception("Failed to regenerate")
        await callback.message.edit_text(
            f"<b>Ошибка</b>\n\n{e}",
            reply_markup=get_compose_back_keyboard(),
        )
        await state.clear()
        return

    chat_history.append({"role": "assistant", "content": result})
    await state.update_data(chat_history=chat_history, last_result=result)
    await callback.message.edit_text(
        f"<b>Результат</b>\n\n{result}",
        reply_markup=get_result_keyboard(),
    )


# ==================== Быстрые доработки: короче / длиннее / другой тон ====================

@router.callback_query(F.data.startswith("cmp:refine:"), ComposeState.refining)
async def quick_refine(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Быстрая доработка по кнопке."""
    action = callback.data.split(":")[2]
    instructions = {
        "shorter": "Сделай сообщение короче, сохрани суть.",
        "longer": "Сделай сообщение длиннее, добавь деталей.",
        "tone": "Измени тон сообщения — сделай более неформальным и дружелюбным.",
    }
    instruction = instructions.get(action, "Переделай.")

    data = await state.get_data()
    chat_history: list[dict] = data.get("chat_history", [])
    msg_type = data.get("msg_type", "broadcast")
    length = data.get("length", "medium")

    chat_history.append({"role": "user", "content": instruction})

    await callback.message.edit_text("<b>Дорабатываю...</b>")
    await callback.answer()

    try:
        result = await _service.refine(
            user_id=user["id"],
            chat_history=chat_history,
            msg_type=msg_type,
            length=length,
        )
    except Exception as e:
        logger.exception("Failed to refine")
        # Убираем неудавшийся запрос из истории
        chat_history.pop()
        await callback.message.edit_text(
            f"<b>Ошибка</b>\n\n{e}",
            reply_markup=get_result_keyboard(),
        )
        return

    chat_history.append({"role": "assistant", "content": result})
    await state.update_data(chat_history=chat_history, last_result=result)
    await callback.message.edit_text(
        f"<b>Результат</b>\n\n{result}",
        reply_markup=get_result_keyboard(),
    )


# ==================== Текстовая доработка ====================

@router.message(ComposeState.refining)
async def text_refine(message: Message, user: dict, state: FSMContext) -> None:
    """Пользователь пишет текстом — доработка результата."""
    text = message.text.strip() if message.text else ""
    if not text:
        return

    await _cleanup(message, state)
    data = await state.get_data()
    chat_history: list[dict] = data.get("chat_history", [])
    msg_type = data.get("msg_type", "broadcast")
    length = data.get("length", "medium")

    chat_history.append({"role": "user", "content": text})

    loading_msg = await message.answer("<b>Дорабатываю...</b>")

    try:
        result = await _service.refine(
            user_id=user["id"],
            chat_history=chat_history,
            msg_type=msg_type,
            length=length,
        )
    except Exception as e:
        logger.exception("Failed to refine via text")
        chat_history.pop()
        await loading_msg.edit_text(
            f"<b>Ошибка</b>\n\n{e}",
            reply_markup=get_result_keyboard(),
        )
        return

    chat_history.append({"role": "assistant", "content": result})
    await state.update_data(
        chat_history=chat_history,
        last_result=result,
        _bot_msg_id=loading_msg.message_id,
    )
    await loading_msg.edit_text(
        f"<b>Результат</b>\n\n{result}",
        reply_markup=get_result_keyboard(),
    )


# ==================== Шаблоны ====================

@router.callback_query(F.data.startswith("cmp:templates:"), StateFilter("*"))
async def show_templates(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Показывает список шаблонов."""
    await state.clear()
    parts = callback.data.split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    templates = _service.get_templates(user["id"])
    if not templates:
        await callback.message.edit_text(
            "<b>Мои шаблоны</b>\n\n"
            "У тебя пока нет сохранённых шаблонов.\n"
            "Сгенерируй сообщение и сохрани его.",
            reply_markup=get_compose_back_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"<b>Мои шаблоны</b> ({len(templates)})\n\n"
        "[R] — рассылка, [O] — отклик",
        reply_markup=get_templates_keyboard(templates, page=page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cmp:tpl:"), StateFilter("*"))
async def show_template_detail(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает полный текст шаблона."""
    await state.clear()
    template_id = callback.data.split(":")[2]

    from db.repositories.messages import MessageRepository
    msg_repo = MessageRepository()
    template = msg_repo.get_by_id(template_id)

    if not template:
        await callback.answer("Шаблон не найден", show_alert=True)
        return

    msg_type = "Рассылка" if template["type"] == "broadcast" else "Отклик"
    await callback.message.edit_text(
        f"<b>Шаблон ({msg_type})</b>\n\n"
        f"{template['content']}",
        reply_markup=get_template_detail_keyboard(template_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cmp:del:"), StateFilter("*"))
async def delete_template(callback: CallbackQuery, user: dict, state: FSMContext) -> None:
    """Удаляет шаблон."""
    template_id = callback.data.split(":")[2]
    _service.delete_template(template_id)
    await callback.answer("Шаблон удалён")

    # Возвращаемся к списку
    templates = _service.get_templates(user["id"])
    if not templates:
        await callback.message.edit_text(
            "<b>Мои шаблоны</b>\n\n"
            "У тебя пока нет сохранённых шаблонов.",
            reply_markup=get_compose_back_keyboard(),
        )
        return

    await callback.message.edit_text(
        f"<b>Мои шаблоны</b> ({len(templates)})\n\n"
        "[R] — рассылка, [O] — отклик",
        reply_markup=get_templates_keyboard(templates, page=0),
    )


# ==================== No-op ====================

@router.callback_query(F.data == "cmp:noop:", StateFilter("*"))
async def noop_handler(callback: CallbackQuery) -> None:
    """Заглушка для информационных кнопок."""
    await callback.answer()
