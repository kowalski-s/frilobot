"""Клавиатуры для модуля «Радар»."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.pagination import MenuCallback, PageCallback

# Префикс для callback data радара
_PREFIX = "rad"

# Назначения каналов
_PURPOSE_LABELS: dict[str, str] = {
    "broadcast": "Рассылка",
    "vacancies": "Вакансии",
    "both": "Оба",
}


def get_radar_menu_keyboard(
    has_channels: bool = False,
    has_profile_keywords: bool = False,
) -> InlineKeyboardMarkup:
    """Главная клавиатура радара: поиск по профилю / свой запрос."""
    buttons: list[list[InlineKeyboardButton]] = []

    if has_profile_keywords:
        buttons.append([InlineKeyboardButton(
            text="Поиск по профилю",
            callback_data=f"{_PREFIX}:profile:",
        )])

    buttons.append([InlineKeyboardButton(
        text="Свой запрос",
        callback_data=f"{_PREFIX}:search:",
    )])
    if has_channels:
        buttons.append([InlineKeyboardButton(
            text="Мои каналы",
            callback_data=f"{_PREFIX}:list:0",
        )])
    buttons.append([InlineKeyboardButton(
        text="\u2190 Меню",
        callback_data=MenuCallback(action="main").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_channel_card_keyboard(channel_id: str) -> InlineKeyboardMarkup:
    """Клавиатура карточки канала: выбор назначения или пропуск."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Рассылка", callback_data=f"{_PREFIX}:link:{channel_id}:broadcast"),
            InlineKeyboardButton(text="Вакансии", callback_data=f"{_PREFIX}:link:{channel_id}:vacancies"),
        ],
        [
            InlineKeyboardButton(text="Оба", callback_data=f"{_PREFIX}:link:{channel_id}:both"),
            InlineKeyboardButton(text="Пропустить", callback_data=f"{_PREFIX}:skip:"),
        ],
    ])


def get_user_channels_keyboard(
    channels: list[dict],
    page: int = 0,
    per_page: int = 5,
) -> InlineKeyboardMarkup:
    """Список подключённых каналов с пагинацией."""
    total = len(channels)
    start = page * per_page
    end = start + per_page
    page_items = channels[start:end]
    total_pages = max(1, (total + per_page - 1) // per_page)

    buttons: list[list[InlineKeyboardButton]] = []

    for item in page_items:
        ch = item.get("channels", {})
        title = ch.get("title") or ch.get("username") or "Без названия"
        purpose = _PURPOSE_LABELS.get(item.get("purpose", ""), item.get("purpose", ""))
        label = f"{title} [{purpose}]"
        # Обрезаем длинные названия
        if len(label) > 45:
            label = label[:42] + "..."
        buttons.append([InlineKeyboardButton(
            text=label,
            callback_data=f"{_PREFIX}:ch:{item['id']}",
        )])

    # Пагинация
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="\u2190",
            callback_data=f"{_PREFIX}:list:{page - 1}",
        ))
    if end < total:
        nav.append(InlineKeyboardButton(
            text="\u2192",
            callback_data=f"{_PREFIX}:list:{page + 1}",
        ))
    if nav:
        buttons.append(nav)

    # Кнопка «Страница X из Y» (информационная)
    if total_pages > 1:
        buttons.append([InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data=f"{_PREFIX}:noop:",
        )])

    buttons.append([InlineKeyboardButton(
        text="\u2190 Радар",
        callback_data=f"{_PREFIX}:back:",
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_channel_manage_keyboard(user_channel_id: str, channel_id: str) -> InlineKeyboardMarkup:
    """Управление подключённым каналом: сменить назначение / отключить."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Рассылка", callback_data=f"{_PREFIX}:purpose:{user_channel_id}:broadcast"),
            InlineKeyboardButton(text="Вакансии", callback_data=f"{_PREFIX}:purpose:{user_channel_id}:vacancies"),
        ],
        [
            InlineKeyboardButton(text="Оба", callback_data=f"{_PREFIX}:purpose:{user_channel_id}:both"),
        ],
        [InlineKeyboardButton(
            text="Отключить канал",
            callback_data=f"{_PREFIX}:unlink:{channel_id}",
        )],
        [InlineKeyboardButton(
            text="\u2190 Мои каналы",
            callback_data=f"{_PREFIX}:list:0",
        )],
    ])


def get_radar_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в радар."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2190 Радар",
            callback_data=f"{_PREFIX}:back:",
        )],
    ])
