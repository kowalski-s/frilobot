"""Клавиатуры для онбординга."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class OnboardingCallback(CallbackData, prefix="onb"):
    """Callback для кнопок онбординга."""

    step: str
    value: str


# --- Специализации (мультивыбор) ---

_SPECIALIZATIONS: list[tuple[str, str]] = [
    ("dev", "Разработка"),
    ("design", "Дизайн"),
    ("marketing", "Маркетинг/SMM"),
    ("copywriting", "Копирайтинг"),
    ("automation", "Автоматизация/боты"),
]


# Маппинг ключ → название для предустановленных специализаций
SPEC_LABELS: dict[str, str] = {key: label for key, label in _SPECIALIZATIONS}


def get_specialization_keyboard(selected: list[str] | None = None) -> InlineKeyboardMarkup:
    """Мультивыбор специализаций. Выбранные помечаются галочкой."""
    selected = selected or []
    rows: list[list[InlineKeyboardButton]] = []

    # Предустановленные
    for key, label in _SPECIALIZATIONS:
        mark = "\u2705 " if key in selected else ""
        rows.append([InlineKeyboardButton(
            text=f"{mark}{label}",
            callback_data=OnboardingCallback(step="spec", value=key).pack(),
        )])

    # Пользовательские (всё, что не в предустановленных)
    for idx, custom in enumerate(selected):
        if custom not in SPEC_LABELS:
            rows.append([InlineKeyboardButton(
                text=f"\u2705 {custom}",
                callback_data=OnboardingCallback(step="spec_del", value=str(idx)).pack(),
            )])

    # Кнопка «Другое»
    rows.append([InlineKeyboardButton(
        text="\u270f\ufe0f Другое (ввести своё)",
        callback_data=OnboardingCallback(step="spec", value="custom").pack(),
    )])
    rows.append([InlineKeyboardButton(
        text="Далее \u2192",
        callback_data=OnboardingCallback(step="spec", value="done").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Бюджет ---

_BUDGETS: list[tuple[str, str]] = [
    ("0", "Любой"),
    ("5000", "от 5 000\u20bd"),
    ("15000", "от 15 000\u20bd"),
    ("50000", "от 50 000\u20bd"),
]


def get_budget_keyboard() -> InlineKeyboardMarkup:
    """Выбор минимального бюджета."""
    rows: list[list[InlineKeyboardButton]] = []
    for value, label in _BUDGETS:
        rows.append([InlineKeyboardButton(
            text=label,
            callback_data=OnboardingCallback(step="budget", value=value).pack(),
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Формат работы (мультивыбор) ---

_WORK_FORMATS: list[tuple[str, str]] = [
    ("oneoff", "Разовые"),
    ("project", "Проекты"),
    ("permanent", "Постоянка"),
]


def get_work_format_keyboard(selected: list[str] | None = None) -> InlineKeyboardMarkup:
    """Мультивыбор формата работы."""
    selected = selected or []
    rows: list[list[InlineKeyboardButton]] = []
    for key, label in _WORK_FORMATS:
        mark = "\u2705 " if key in selected else ""
        rows.append([InlineKeyboardButton(
            text=f"{mark}{label}",
            callback_data=OnboardingCallback(step="format", value=key).pack(),
        )])
    rows.append([InlineKeyboardButton(
        text="Далее \u2192",
        callback_data=OnboardingCallback(step="format", value="done").pack(),
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Дисклеймер ---

def get_disclaimer_keyboard() -> InlineKeyboardMarkup:
    """Принятие рисков рассылки."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\u2705 Принимаю риски",
            callback_data=OnboardingCallback(step="disclaimer", value="accept").pack(),
        )],
        [InlineKeyboardButton(
            text="\u274c Не буду использовать рассылку",
            callback_data=OnboardingCallback(step="disclaimer", value="decline").pack(),
        )],
    ])


# --- Кнопка «Начать настройку» ---

def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """Кнопка начала онбординга."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="\ud83d\ude80 Начать настройку",
            callback_data=OnboardingCallback(step="welcome", value="start").pack(),
        )],
    ])
