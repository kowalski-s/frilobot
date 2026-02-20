"""Клавиатуры для модуля «Составить текст» (чат-формат)."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.pagination import MenuCallback

# Префикс для callback data
_PREFIX = "cmp"


def get_compose_menu_keyboard(has_templates: bool = False) -> InlineKeyboardMarkup:
    """Главная клавиатура модуля: выбор действия."""
    buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text="Сообщение для рассылки",
            callback_data=f"{_PREFIX}:broadcast:",
        )],
        [InlineKeyboardButton(
            text="Отклик на вакансию",
            callback_data=f"{_PREFIX}:vacancy:",
        )],
    ]
    if has_templates:
        buttons.append([InlineKeyboardButton(
            text="Мои шаблоны",
            callback_data=f"{_PREFIX}:templates:0",
        )])
    buttons.append([InlineKeyboardButton(
        text="\u2190 Меню",
        callback_data=MenuCallback(action="main").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_chat_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура сбора инфо для рассылки (до генерации).

    Кнопки длины + «Сгенерировать по профилю» + «Назад».
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Короткое", callback_data=f"{_PREFIX}:len:short"),
            InlineKeyboardButton(text="Среднее", callback_data=f"{_PREFIX}:len:medium"),
            InlineKeyboardButton(text="Длинное", callback_data=f"{_PREFIX}:len:long"),
        ],
        [InlineKeyboardButton(
            text="Сгенерировать по профилю",
            callback_data=f"{_PREFIX}:from_profile:",
        )],
        [InlineKeyboardButton(
            text="\u2190 Назад",
            callback_data=f"{_PREFIX}:back:",
        )],
    ])


def get_vacancy_chat_keyboard(can_generate: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура сбора инфо для отклика.

    После вставки вакансии показывает «Сгенерировать».
    """
    buttons: list[list[InlineKeyboardButton]] = []
    if can_generate:
        buttons.append([InlineKeyboardButton(
            text="Сгенерировать",
            callback_data=f"{_PREFIX}:gen_vacancy:",
        )])
    buttons.append([InlineKeyboardButton(
        text="\u2190 Назад",
        callback_data=f"{_PREFIX}:back:",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_result_keyboard() -> InlineKeyboardMarkup:
    """Панель действий после генерации результата."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сохранить", callback_data=f"{_PREFIX}:save:"),
            InlineKeyboardButton(text="Переделать", callback_data=f"{_PREFIX}:regen:"),
        ],
        [
            InlineKeyboardButton(text="Короче", callback_data=f"{_PREFIX}:refine:shorter"),
            InlineKeyboardButton(text="Длиннее", callback_data=f"{_PREFIX}:refine:longer"),
            InlineKeyboardButton(text="Другой тон", callback_data=f"{_PREFIX}:refine:tone"),
        ],
        [InlineKeyboardButton(
            text="\u2190 Меню",
            callback_data=f"{_PREFIX}:back:",
        )],
    ])


def get_templates_keyboard(
    templates: list[dict],
    page: int = 0,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    """Список шаблонов с пагинацией."""
    total = len(templates)
    start = page * per_page
    end = start + per_page
    page_items = templates[start:end]

    buttons: list[list[InlineKeyboardButton]] = []

    for tpl in page_items:
        # Превью текста — первые 35 символов
        preview = tpl["content"][:35].replace("\n", " ")
        if len(tpl["content"]) > 35:
            preview += "..."
        msg_type = "R" if tpl["type"] == "broadcast" else "O"
        buttons.append([InlineKeyboardButton(
            text=f"[{msg_type}] {preview}",
            callback_data=f"{_PREFIX}:tpl:{tpl['id']}",
        )])

    # Пагинация
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="\u2190",
            callback_data=f"{_PREFIX}:templates:{page - 1}",
        ))
    if end < total:
        nav.append(InlineKeyboardButton(
            text="\u2192",
            callback_data=f"{_PREFIX}:templates:{page + 1}",
        ))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(
        text="\u2190 Назад",
        callback_data=f"{_PREFIX}:back:",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_template_detail_keyboard(template_id: str) -> InlineKeyboardMarkup:
    """Клавиатура просмотра шаблона: удалить, назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Удалить",
            callback_data=f"{_PREFIX}:del:{template_id}",
        )],
        [InlineKeyboardButton(
            text="\u2190 Шаблоны",
            callback_data=f"{_PREFIX}:templates:0",
        )],
    ])


def get_compose_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в меню составления текста."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2190 Назад",
            callback_data=f"{_PREFIX}:back:",
        )],
    ])
