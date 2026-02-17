"""Хендлер главного меню — обработка нажатий на кнопки."""

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks.pagination import MenuCallback
from bot.keyboards.menu import get_main_menu_keyboard

router = Router(name="menu")

# Заголовки разделов для заглушек
_SECTION_TITLES: dict[str, str] = {
    "radar": "Радар",
    "compose": "Составить текст",
    "vacancies": "Найти заказы",
    "broadcast": "Рассылка",
    "profile": "Мой профиль",
    "settings": "Настройки",
}


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2190 Меню",
            callback_data=MenuCallback(action="main").pack(),
        )],
    ])


@router.callback_query(MenuCallback.filter(F.action == "main"))
async def back_to_menu(callback: CallbackQuery, user: dict) -> None:
    """Возврат в главное меню."""
    name = user.get("first_name") or "друг"
    await callback.message.edit_text(
        f"Привет, {name}! Что делаем?",
        reply_markup=get_main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(MenuCallback.filter())
async def menu_callback(callback: CallbackQuery, callback_data: MenuCallback) -> None:
    """Обработка нажатий на кнопки главного меню (заглушки)."""
    section = _SECTION_TITLES.get(callback_data.action, callback_data.action)
    await callback.message.edit_text(
        f"<b>{section}</b>\n\nРаздел в разработке.",
        reply_markup=get_back_to_menu_keyboard(),
    )
    await callback.answer()
