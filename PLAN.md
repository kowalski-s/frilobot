# Frilo — План разработки

> Каждая задача — атомарная. Выполняется по одной, последовательно. После каждой задачи проект должен запускаться без ошибок.

---

## ~~Фаза 1 — Структура проекта и окружение~~ ✅

### ~~Задача 1.1: Инициализация проекта~~ ✅

**Что создаётся:** базовая структура папок, конфигурационные файлы, gitignore.

**Файлы:**
- `pyproject.toml` — метаданные проекта, зависимости, настройки ruff
- `requirements.txt` — зависимости (aiogram, supabase, apscheduler, aiohttp, bs4, python-dotenv)
- `.env.example` — шаблон переменных окружения
- `.gitignore` — Python-стандарт + .env, __pycache__, .venv, sessions/

**Результат:** проект можно склонировать, создать venv, установить зависимости.

**Проверка:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Без ошибок
```

---

### ~~Задача 1.2: Структура пакетов~~ ✅

**Что создаётся:** все пакеты (папки с `__init__.py`) согласно структуре из CLAUDE.md. Файлы пока пустые — только `__init__.py`.

**Файлы:**
- `bot/__init__.py`
- `bot/handlers/__init__.py`
- `bot/keyboards/__init__.py`
- `bot/states/__init__.py`
- `bot/middlewares/__init__.py`
- `bot/filters/__init__.py`
- `bot/callbacks/__init__.py`
- `services/__init__.py`
- `llm/__init__.py`
- `llm/prompts/__init__.py`
- `db/__init__.py`
- `db/repositories/__init__.py`
- `scheduler/__init__.py`
- `parsers/__init__.py`
- `userbot/__init__.py`
- `utils/__init__.py`
- `migrations/`

**Результат:** все импорты пакетов работают, структура видна в файловом дереве.

**Проверка:**
```bash
python -c "import bot; import services; import db; import llm; import parsers; import scheduler; import utils"
# Без ошибок
```

---

### ~~Задача 1.3: Конфиг и переменные окружения~~ ✅

**Что создаётся:** модуль конфигурации, загрузка .env.

**Файлы:**
- `bot/config.py` — dataclass `Settings` с полями: `BOT_TOKEN`, `ADMIN_IDS` (list[int]), `SUPABASE_URL`, `SUPABASE_KEY`, `LLM_API_KEY`, `LLM_MODEL`, `DEFAULT_BROADCAST_LIMIT`, `DEFAULT_MIN_DELAY`, `DEFAULT_MAX_DELAY`. Загрузка из env через `python-dotenv`. Валидация: если `BOT_TOKEN` пустой — raise с понятным сообщением.

**Результат:** `from bot.config import settings` — работает, значения читаются из `.env`.

**Проверка:**
```bash
cp .env.example .env
# Заполнить BOT_TOKEN
python -c "from bot.config import settings; print(settings.BOT_TOKEN)"
# Выводит токен
```

---

### ~~Задача 1.4: Точка входа и запуск пустого бота~~ ✅

**Что создаётся:** минимальный запуск aiogram-бота, который стартует и слушает обновления.

**Файлы:**
- `bot/__main__.py` — создание `Bot`, `Dispatcher`, запуск polling. Настройка логирования (INFO). Импорт конфига.

**Результат:** бот запускается, подключается к Telegram, в логах `Bot started`. Ctrl+C — корректное завершение.

**Проверка:**
```bash
python -m bot
# В логах: "Bot started" или аналогичное от aiogram
# Ctrl+C — "Bot stopped", без traceback
```

---

## Фаза 2 — База данных

### Задача 2.1: Подключение к Supabase

**Что создаётся:** модуль подключения к БД через supabase-py.

**Файлы:**
- `db/connection.py` — асинхронная функция `get_supabase_client()`, возвращает клиент Supabase. Singleton-паттерн (один клиент на приложение).

**Результат:** из любого модуля можно получить клиент Supabase.

**Проверка:**
```bash
python -c "
import asyncio
from db.connection import get_supabase_client
client = get_supabase_client()
print('Connected:', client is not None)
"
# Connected: True
```

---

### Задача 2.2: SQL-миграция — таблицы users, settings, search_profiles

**Что создаётся:** SQL-файл с таблицами для пользователей.

**Файлы:**
- `migrations/001_users.sql` — CREATE TABLE `users`, `settings`, `search_profiles` со всеми полями, типами, ограничениями, индексами из PRD.md раздел 6.

**Таблицы:**
- `users` — 12 полей (id UUID PK, telegram_id BIGINT UNIQUE, username, first_name, specializations TEXT[], services_description, portfolio_url, onboarding_completed, disclaimer_accepted, is_admin, subscription_tier, created_at, updated_at)
- `settings` — 7 полей (id, user_id FK UNIQUE, broadcast_limit_per_hour, quiet_hours_start, quiet_hours_end, min_delay_seconds, max_delay_seconds, updated_at)
- `search_profiles` — 6 полей (id, user_id FK, keywords TEXT[], min_budget, work_format TEXT[], is_active, created_at)

**Результат:** SQL выполняется в Supabase SQL Editor без ошибок.

**Проверка:**
- Открыть Supabase Dashboard → SQL Editor → вставить содержимое файла → Run
- В Table Editor появились 3 таблицы с правильными колонками
- Попробовать вставить тестовую строку в `users` — ОК

---

### Задача 2.3: SQL-миграция — таблицы channels, user_channels

**Что создаётся:** таблицы для каналов.

**Файлы:**
- `migrations/002_channels.sql` — CREATE TABLE `channels`, `user_channels`.

**Таблицы:**
- `channels` — 10 полей (id, telegram_id BIGINT UNIQUE, username, title, description, subscribers_count, is_paid, category, source, last_parsed_at, created_at)
- `user_channels` — 5 полей (id, user_id FK, channel_id FK, purpose, is_active, created_at). UNIQUE(user_id, channel_id).

**Результат:** таблицы созданы, FK-связи работают.

**Проверка:**
- SQL Editor → Run → без ошибок
- Вставить канал в `channels`, потом связать с пользователем в `user_channels` — ОК
- Попробовать дубликат (user_id, channel_id) — ошибка UNIQUE constraint

---

### Задача 2.4: SQL-миграция — таблицы messages, broadcasts, broadcast_items

**Что создаётся:** таблицы для сообщений и рассылок.

**Файлы:**
- `migrations/003_broadcasts.sql` — CREATE TABLE `messages`, `broadcasts`, `broadcast_items`.

**Таблицы:**
- `messages` — 6 полей (id, user_id FK, type, content, is_template, metadata JSONB, created_at)
- `broadcasts` — 9 полей (id, user_id FK, message_id FK, status, total_channels, sent_count, error_count, started_at, completed_at, created_at)
- `broadcast_items` — 7 полей (id, broadcast_id FK, user_channel_id FK, status, sent_at, error_message, unique_content, created_at)

**Результат:** таблицы созданы, FK-цепочка broadcasts → messages и broadcast_items → user_channels работает.

**Проверка:**
- SQL Editor → Run → без ошибок
- Создать message → broadcast с этим message_id → broadcast_item с этим broadcast_id — ОК

---

### Задача 2.5: SQL-миграция — таблицы channel_messages, saved_vacancies

**Что создаётся:** таблицы для вакансий.

**Файлы:**
- `migrations/004_vacancies.sql` — CREATE TABLE `channel_messages`, `saved_vacancies`.

**Таблицы:**
- `channel_messages` — 7 полей (id, channel_id FK, telegram_message_id BIGINT, text, date, is_vacancy BOOLEAN NULL, vacancy_data JSONB, created_at). UNIQUE(channel_id, telegram_message_id).
- `saved_vacancies` — 5 полей (id, user_id FK, channel_message_id FK, status, response_text, created_at)

**Результат:** все 10 таблиц из PRD созданы. Полная схема БД готова.

**Проверка:**
- SQL Editor → Run → без ошибок
- В Table Editor — 10 таблиц
- Проверить FK: saved_vacancies.channel_message_id ссылается на channel_messages.id — ОК

---

### Задача 2.6: Репозиторий users

**Что создаётся:** CRUD-операции для таблицы `users`.

**Файлы:**
- `db/repositories/users.py` — класс `UserRepository` с методами:
  - `get_by_telegram_id(telegram_id: int) -> dict | None`
  - `create(telegram_id: int, username: str, first_name: str) -> dict`
  - `update(user_id: str, **fields) -> dict`
  - `complete_onboarding(user_id: str) -> None`
  - `accept_disclaimer(user_id: str) -> None`

**Результат:** можно создавать, читать и обновлять пользователей через Python-код.

**Проверка:**
```bash
python -c "
from db.repositories.users import UserRepository
repo = UserRepository()
# Создать пользователя
user = repo.create(telegram_id=123456, username='test', first_name='Тест')
print('Created:', user['id'])
# Найти по telegram_id
found = repo.get_by_telegram_id(123456)
print('Found:', found['username'])
# Обновить
repo.update(user['id'], specializations=['dev', 'design'])
"
```

---

### Задача 2.7: Репозиторий settings

**Что создаётся:** CRUD для пользовательских настроек.

**Файлы:**
- `db/repositories/settings.py` — класс `SettingsRepository`:
  - `get_by_user_id(user_id: str) -> dict | None`
  - `create_default(user_id: str) -> dict` — создаёт запись с дефолтными значениями
  - `update(user_id: str, **fields) -> dict`

**Результат:** при создании пользователя можно сразу создать дефолтные настройки.

**Проверка:**
```bash
python -c "
from db.repositories.settings import SettingsRepository
repo = SettingsRepository()
s = repo.create_default(user_id='...')
print('Limit:', s['broadcast_limit_per_hour'])  # 5
"
```

---

### Задача 2.8: Репозиторий channels и user_channels

**Что создаётся:** CRUD для каналов и связей с пользователями.

**Файлы:**
- `db/repositories/channels.py` — класс `ChannelRepository`:
  - `get_or_create(telegram_id: int, username: str, title: str, **kwargs) -> dict`
  - `get_by_username(username: str) -> dict | None`
  - `update(channel_id: str, **fields) -> dict`
  - `link_to_user(user_id: str, channel_id: str, purpose: str) -> dict` — создаёт запись в `user_channels`
  - `unlink_from_user(user_id: str, channel_id: str) -> None`
  - `get_user_channels(user_id: str, purpose: str | None = None) -> list[dict]` — каналы пользователя, опционально фильтр по purpose
  - `update_user_channel_purpose(user_channel_id: str, purpose: str) -> dict`

**Результат:** полный цикл работы с каналами: создать канал → привязать к пользователю → получить список → отвязать.

**Проверка:**
```bash
python -c "
from db.repositories.channels import ChannelRepository
repo = ChannelRepository()
ch = repo.get_or_create(telegram_id=-100123, username='test_channel', title='Тест')
repo.link_to_user(user_id='...', channel_id=ch['id'], purpose='broadcast')
channels = repo.get_user_channels(user_id='...', purpose='broadcast')
print('Broadcast channels:', len(channels))
"
```

---

### Задача 2.9: Репозиторий messages

**Что создаётся:** CRUD для сообщений (шаблонов рассылки, откликов).

**Файлы:**
- `db/repositories/messages.py` — класс `MessageRepository`:
  - `create(user_id: str, type: str, content: str, is_template: bool = False, metadata: dict | None = None) -> dict`
  - `get_by_id(message_id: str) -> dict | None`
  - `get_user_templates(user_id: str) -> list[dict]`
  - `update_content(message_id: str, content: str) -> dict`
  - `delete(message_id: str) -> None`

**Результат:** можно сохранять, редактировать и удалять шаблоны сообщений.

**Проверка:**
```bash
python -c "
from db.repositories.messages import MessageRepository
repo = MessageRepository()
msg = repo.create(user_id='...', type='broadcast', content='Текст', is_template=True)
templates = repo.get_user_templates(user_id='...')
print('Templates:', len(templates))
"
```

---

### Задача 2.10: Репозиторий broadcasts

**Что создаётся:** CRUD для рассылок и их элементов.

**Файлы:**
- `db/repositories/broadcasts.py` — класс `BroadcastRepository`:
  - `create(user_id: str, message_id: str, channel_ids: list[str]) -> dict` — создаёт `broadcasts` + `broadcast_items` для каждого канала
  - `get_active(user_id: str) -> dict | None` — текущая активная рассылка
  - `get_history(user_id: str, limit: int = 10) -> list[dict]`
  - `update_status(broadcast_id: str, status: str) -> None`
  - `get_pending_items(broadcast_id: str, limit: int = 1) -> list[dict]` — следующие элементы для отправки
  - `mark_item_sent(item_id: str) -> None`
  - `mark_item_failed(item_id: str, error: str) -> None`
  - `increment_sent_count(broadcast_id: str) -> None`
  - `increment_error_count(broadcast_id: str) -> None`

**Результат:** полный цикл рассылки через БД: создать → получить pending → отметить sent/failed → обновить счётчики.

**Проверка:**
```bash
python -c "
from db.repositories.broadcasts import BroadcastRepository
repo = BroadcastRepository()
bc = repo.create(user_id='...', message_id='...', channel_ids=['...', '...'])
print('Broadcast:', bc['status'])  # pending
items = repo.get_pending_items(bc['id'])
print('Pending items:', len(items))  # 2
"
```

---

### Задача 2.11: Репозиторий vacancies

**Что создаётся:** CRUD для спарсенных сообщений и сохранённых вакансий.

**Файлы:**
- `db/repositories/vacancies.py` — класс `VacancyRepository`:
  - `save_channel_messages(channel_id: str, messages: list[dict]) -> int` — bulk upsert в `channel_messages`, возвращает кол-во новых
  - `get_unfiltered(channel_ids: list[str], limit: int = 100) -> list[dict]` — сообщения где `is_vacancy IS NULL`
  - `mark_as_vacancy(message_id: str, vacancy_data: dict) -> None`
  - `mark_as_not_vacancy(message_id: str) -> None`
  - `get_vacancies(channel_ids: list[str], limit: int = 10) -> list[dict]` — подтверждённые вакансии
  - `save_vacancy(user_id: str, channel_message_id: str) -> dict` — в избранное
  - `get_saved(user_id: str) -> list[dict]`
  - `update_saved_status(saved_id: str, status: str, response_text: str | None = None) -> None`

**Результат:** полный цикл вакансий: сохранить сырые сообщения → отфильтровать → пометить как вакансию → сохранить в избранное.

**Проверка:**
```bash
python -c "
from db.repositories.vacancies import VacancyRepository
repo = VacancyRepository()
count = repo.save_channel_messages('...', [{'telegram_message_id': 1, 'text': 'Ищу разработчика', 'date': '...'}])
print('New messages:', count)
unfiltered = repo.get_unfiltered(['...'])
print('To filter:', len(unfiltered))
"
```

---

### Задача 2.12: Репозиторий search_profiles

**Что создаётся:** CRUD для профилей поиска.

**Файлы:**
- `db/repositories/search_profiles.py` — класс `SearchProfileRepository`:
  - `create(user_id: str, keywords: list[str], min_budget: int | None, work_format: list[str]) -> dict`
  - `get_active(user_id: str) -> dict | None`
  - `update(profile_id: str, **fields) -> dict`

**Результат:** можно создавать и редактировать профили поиска.

**Проверка:**
```bash
python -c "
from db.repositories.search_profiles import SearchProfileRepository
repo = SearchProfileRepository()
sp = repo.create(user_id='...', keywords=['python', 'бот'], min_budget=15000, work_format=['project'])
print('Profile:', sp['keywords'])
"
```

---

## Фаза 3 — Бот: базовый каркас

### Задача 3.1: Мидлварь авторизации

**Что создаётся:** middleware, который при каждом сообщении проверяет пользователя в БД, создаёт если нет, и кладёт `user` в `data`.

**Файлы:**
- `bot/middlewares/auth.py` — класс `AuthMiddleware(BaseMiddleware)`:
  - На каждое обновление: `UserRepository.get_by_telegram_id()`. Если нет — `create()` + `SettingsRepository.create_default()`.
  - Кладёт `data["user"]` — dict с данными пользователя.

**Результат:** в любом хендлере доступен `user = data["user"]` с полным профилем из БД.

**Проверка:**
- Написать боту любое сообщение
- В Supabase Table Editor → таблица `users` — появилась новая строка с telegram_id
- В таблице `settings` — строка с дефолтными настройками для этого user_id

---

### Задача 3.2: Мидлварь антифлуда

**Что создаётся:** простой throttling — не более 1 сообщения в секунду от одного пользователя.

**Файлы:**
- `bot/middlewares/throttling.py` — класс `ThrottlingMiddleware(BaseMiddleware)`:
  - Хранит dict `{user_id: last_message_time}` в памяти
  - Если < 1 сек с прошлого — игнорирует обновление

**Результат:** быстрый флуд от пользователя не нагружает бота.

**Проверка:**
- Быстро отправить 5 сообщений подряд — бот обработает только первое, остальные проигнорирует
- Подождать секунду, отправить ещё — обработает

---

### Задача 3.3: Фильтр админа

**Что создаётся:** фильтр для ограничения хендлеров только админами.

**Файлы:**
- `bot/filters/admin.py` — класс `IsAdmin(Filter)`:
  - Проверяет `user["is_admin"]` из data (от AuthMiddleware)
  - Или проверяет `telegram_id in settings.ADMIN_IDS`

**Результат:** можно навесить `IsAdmin()` на хендлер — он сработает только для админов.

**Проверка:**
- Создать тестовый хендлер с фильтром `IsAdmin()`
- Написать от своего аккаунта (ID в ADMIN_IDS) — ответит
- Написать от другого аккаунта — проигнорирует

---

### Задача 3.4: Callback data factories и пагинация

**Что создаётся:** базовые callback data для навигации и пагинации.

**Файлы:**
- `bot/callbacks/pagination.py`:
  - `MenuCallback(CallbackData)` — prefix `menu`, field `action` (строка)
  - `PageCallback(CallbackData)` — prefix `page`, fields `section` (строка), `page` (int)

**Результат:** типизированные callback data для кнопок меню и пагинации.

**Проверка:**
```bash
python -c "
from bot.callbacks.pagination import MenuCallback, PageCallback
cb = MenuCallback(action='radar')
print(cb.pack())  # 'menu:radar'
parsed = MenuCallback.unpack('menu:radar')
print(parsed.action)  # 'radar'
"
```

---

### Задача 3.5: Клавиатура главного меню

**Что создаётся:** inline-клавиатура главного меню с 6 кнопками.

**Файлы:**
- `bot/keyboards/menu.py` — функция `get_main_menu_keyboard() -> InlineKeyboardMarkup`:
  - Кнопки в 2 колонки: Радар | Составить текст / Найти заказы | Рассылка / Мой профиль | Настройки
  - Callback data через `MenuCallback`

**Результат:** клавиатура готова к использованию в хендлерах.

**Проверка:**
```bash
python -c "
from bot.keyboards.menu import get_main_menu_keyboard
kb = get_main_menu_keyboard()
print(len(kb.inline_keyboard))  # 3 ряда по 2 кнопки
"
```

---

### Задача 3.6: Хендлер /start и главное меню

**Что создаётся:** обработчик команды /start. Если онбординг пройден — показывает главное меню. Если нет — пока тоже показывает меню (онбординг будет в следующей задаче).

**Файлы:**
- `bot/handlers/start.py` — хендлер `cmd_start`:
  - Приветственное сообщение с именем пользователя
  - Показывает inline-клавиатуру главного меню
- `bot/handlers/menu.py` — хендлер `menu_callback`:
  - Обрабатывает нажатия на кнопки главного меню
  - Пока заглушки: «Раздел в разработке»
- `bot/handlers/__init__.py` — функция `register_all_handlers(dp)` для регистрации всех роутеров
- Обновить `bot/__main__.py` — подключить мидлвари и хендлеры

**Результат:** бот отвечает на /start, показывает меню с 6 кнопками. Нажатие на кнопку — «Раздел в разработке».

**Проверка:**
- Отправить /start → сообщение «Привет, {имя}! Что делаем?» + 6 кнопок
- Нажать «Радар» → «Раздел в разработке»
- Нажать «Мой профиль» → «Раздел в разработке»

---

### Задача 3.7: FSM и клавиатуры онбординга

**Что создаётся:** состояния и клавиатуры для 7 шагов онбординга.

**Файлы:**
- `bot/states/onboarding.py` — `OnboardingState(StatesGroup)`:
  - `welcome`, `specialization`, `services`, `search_keywords`, `search_budget`, `search_format`, `channels`, `disclaimer`
- `bot/keyboards/onboarding.py`:
  - `get_specialization_keyboard()` — мультивыбор: Разработка, Дизайн, Маркетинг/SMM, Копирайтинг, Автоматизация/боты + «Далее»
  - `get_budget_keyboard()` — Любой, от 5000₽, от 15000₽, от 50000₽
  - `get_work_format_keyboard()` — мультивыбор: Разовые, Проекты, Постоянка + «Далее»
  - `get_disclaimer_keyboard()` — Принимаю риски / Не буду использовать рассылку

**Результат:** состояния и клавиатуры готовы к использованию в хендлере онбординга.

**Проверка:**
```bash
python -c "
from bot.states.onboarding import OnboardingState
print(OnboardingState.__all_states__)  # список состояний
from bot.keyboards.onboarding import get_specialization_keyboard
kb = get_specialization_keyboard()
print(len(kb.inline_keyboard))  # кнопки специализаций
"
```

---

### Задача 3.8: Хендлер онбординга

**Что создаётся:** полный флоу онбординга из 7 шагов. Каждый шаг — отдельная функция-хендлер.

**Файлы:**
- `bot/handlers/start.py` — расширить:
  - Если `user["onboarding_completed"] == False` → запустить FSM онбординга
  - Шаг 1 (welcome): приветствие + кнопка «Начать настройку»
  - Шаг 2 (specialization): мультивыбор специализаций, сохранение в state data
  - Шаг 3 (services): ввод текстом описания услуг
  - Шаг 4 (search_keywords): ввод ключевых слов через запятую
  - Шаг 5 (search_budget): выбор минимального бюджета кнопками
  - Шаг 6 (search_format): мультивыбор формата работы
  - Шаг 7 (disclaimer): принятие рисков рассылки
  - Финал: сохранение всего в БД (`UserRepository.update()`, `SearchProfileRepository.create()`), `complete_onboarding()`, показ главного меню

**Результат:** новый пользователь проходит онбординг за 7 шагов, данные сохраняются в БД.

**Проверка:**
- Удалить свою строку из таблицы `users` в Supabase
- Отправить /start → начинается онбординг
- Пройти все 7 шагов
- В Supabase: `users` — заполнены specializations, services_description, onboarding_completed=true, disclaimer_accepted
- В Supabase: `search_profiles` — создан профиль с keywords, min_budget, work_format
- Отправить /start ещё раз → сразу главное меню (без онбординга)

---

## Фаза 4 — Модуль «Мой профиль»

### Задача 4.1: Клавиатуры профиля

**Файлы:**
- `bot/keyboards/profile.py`:
  - `get_profile_keyboard()` — кнопки: Редактировать специализации, Редактировать описание, Редактировать параметры поиска, ← Меню

**Проверка:** импорт без ошибок, количество кнопок соответствует.

---

### Задача 4.2: Хендлер просмотра и редактирования профиля

**Файлы:**
- `bot/handlers/profile.py`:
  - Показ профиля: специализации, описание, портфолио, ключевые слова, бюджет, формат
  - Редактирование каждого поля через FSM (ввод нового значения → сохранение в БД)

**Результат:** пользователь видит свой профиль и может редактировать любое поле.

**Проверка:**
- Нажать «Мой профиль» в меню → видит свои данные из онбординга
- Нажать «Редактировать описание» → ввести новый текст → сообщение «Обновлено»
- Нажать «Мой профиль» → видит обновлённый текст
- В Supabase: `users.services_description` обновилось

---

## Фаза 5 — Модуль «Настройки»

### Задача 5.1: Хендлер настроек

**Файлы:**
- `bot/keyboards/settings.py` — клавиатуры для настроек
- `bot/handlers/settings.py`:
  - Показ текущих настроек (лимит, тихие часы, задержки)
  - Изменение лимита рассылки (inline-кнопки: 3, 5, 10)
  - Изменение тихих часов (ввод текстом «23:00-08:00»)

**Результат:** пользователь видит и меняет настройки рассылки.

**Проверка:**
- Нажать «Настройки» → видит текущие значения (дефолтные)
- Изменить лимит на 10 → «Обновлено»
- В Supabase: `settings.broadcast_limit_per_hour` = 10

---

## Фаза 6 — Модуль «Радар»

### Задача 6.1: Парсер tgstat.ru

**Файлы:**
- `parsers/tgstat.py` — класс `TgstatParser`:
  - `search(query: str, limit: int = 20) -> list[dict]` — поиск каналов, возвращает list с полями: username, title, description, subscribers_count, category
  - Использует aiohttp + BeautifulSoup4
  - Обработка ошибок: timeout, 403, изменение вёрстки → пустой список + лог

**Результат:** можно искать каналы по ключевому слову и получать структурированный результат.

**Проверка:**
```bash
python -c "
import asyncio
from parsers.tgstat import TgstatParser
parser = TgstatParser()
results = asyncio.run(parser.search('python разработка'))
for r in results[:3]:
    print(r['username'], r['subscribers_count'])
"
```

---

### Задача 6.2: Сервис радара

**Файлы:**
- `services/radar.py` — класс `RadarService`:
  - `search_channels(query: str) -> list[dict]` — ищет через TgstatParser, для каждого результата вызывает `ChannelRepository.get_or_create()`, возвращает список каналов из БД
  - `add_channel_by_username(username: str) -> dict | None` — ручное добавление канала

**Результат:** поиск каналов с автоматическим сохранением в БД.

**Проверка:**
```bash
python -c "
import asyncio
from services.radar import RadarService
svc = RadarService()
channels = asyncio.run(svc.search_channels('дизайн'))
print('Found:', len(channels))
# В Supabase: таблица channels пополнилась
"
```

---

### Задача 6.3: Клавиатуры и хендлер радара

**Файлы:**
- `bot/keyboards/radar.py` — клавиатуры для радара (поиск, карточки каналов, управление)
- `bot/handlers/radar.py`:
  - Экран: список подключённых каналов
  - Кнопка «Найти новые» → ввод запроса → результаты с пагинацией
  - Карточка канала: кнопки «Рассылка» / «Вакансии» / «Оба» / «Пропустить»
  - Управление: изменить назначение, отключить

**Результат:** пользователь ищет каналы, подключает их с нужным назначением, управляет списком.

**Проверка:**
- «Радар» → «Найти новые каналы» → ввести «python» → список каналов
- Нажать «Рассылка» на канале → «Канал подключён для рассылки»
- В Supabase: `user_channels` — новая запись с purpose='broadcast'
- «Радар» → видит подключённый канал в списке

---

## Фаза 7 — LLM-интеграция

### Задача 7.1: Клиент LLM

**Файлы:**
- `llm/client.py` — класс `LLMClient`:
  - `__init__(api_key, model)` — из конфига
  - `generate(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str` — один запрос к LLM API
  - `generate_variants(system_prompt: str, user_prompt: str, count: int = 3) -> list[str]` — несколько вариантов
  - Обработка ошибок: timeout, rate limit, невалидный ответ

**Результат:** единая точка для всех LLM-запросов. Смена провайдера — замена этого файла.

**Проверка:**
```bash
python -c "
import asyncio
from llm.client import LLMClient
client = LLMClient()
result = asyncio.run(client.generate('Ты помощник', 'Скажи привет'))
print(result)
"
```

---

### Задача 7.2: Промпт генерации рассылочного сообщения

**Файлы:**
- `llm/prompts/broadcast_message.py`:
  - `build_prompt(user_profile: dict, target_channel: dict | None = None) -> tuple[str, str]` — возвращает (system_prompt, user_prompt)
  - System prompt: роль копирайтера, знание AIDA/PAS, антиспам-правила, формат
  - User prompt: данные профиля, канал (если есть), требования

**Результат:** промпт генерирует качественные рассылочные сообщения.

**Проверка:**
```bash
python -c "
from llm.prompts.broadcast_message import build_prompt
system, user = build_prompt({'specializations': ['dev'], 'services_description': 'Делаю ботов'})
print(system[:100])
print(user[:100])
"
```

---

### Задача 7.3: Промпт генерации отклика на вакансию

**Файлы:**
- `llm/prompts/vacancy_response.py`:
  - `build_prompt(user_profile: dict, vacancy_text: str) -> tuple[str, str]`
  - System prompt: роль рекрутера/карьерного консультанта, структура отклика
  - User prompt: профиль + текст вакансии

**Результат:** промпт генерирует персонализированные отклики.

**Проверка:** аналогично 7.2 — вывести сгенерированные промпты, убедиться что они содержат данные профиля и вакансии.

---

### Задача 7.4: Промпт классификации вакансии

**Файлы:**
- `llm/prompts/vacancy_classify.py`:
  - `build_prompt(message_text: str, user_keywords: list[str]) -> tuple[str, str]`
  - System prompt: роль классификатора, JSON-формат ответа
  - Ожидаемый ответ LLM: `{"is_vacancy": true/false, "title": "...", "budget": "...", "skills": [...]}`

**Результат:** промпт для определения, является ли сообщение вакансией.

**Проверка:** аналогично — вывести промпты, проверить формат.

---

### Задача 7.5: Промпт уникализации текста

**Файлы:**
- `llm/prompts/rewrite.py`:
  - `build_prompt(original_text: str, channel_info: dict | None = None) -> tuple[str, str]`
  - System prompt: сделать рерайт, сохранить смысл, изменить формулировки, адаптировать под канал

**Результат:** промпт для уникализации сообщений перед рассылкой.

**Проверка:** аналогично — вывести промпты.

---

## Фаза 8 — Модуль «Составить текст»

### Задача 8.1: Сервис composer

**Файлы:**
- `services/composer.py` — класс `ComposerService`:
  - `generate_broadcast_messages(user_id: str, channel_id: str | None = None, count: int = 3) -> list[str]` — генерирует варианты рассылочных сообщений
  - `generate_vacancy_response(user_id: str, vacancy_text: str) -> str` — генерирует отклик на вакансию
  - `save_as_template(user_id: str, content: str, type: str) -> dict` — сохраняет в messages с is_template=True

Внутри: берёт профиль из `UserRepository`, строит промпт, вызывает `LLMClient`.

**Результат:** бизнес-логика генерации текстов отделена от бота.

**Проверка:**
```bash
python -c "
import asyncio
from services.composer import ComposerService
svc = ComposerService()
variants = asyncio.run(svc.generate_broadcast_messages(user_id='...'))
for v in variants:
    print(v[:80], '...')
"
```

---

### Задача 8.2: Клавиатуры и FSM составления текста

**Файлы:**
- `bot/keyboards/compose.py` — клавиатуры: выбор действия, выбор каналов, варианты сообщений, подтверждение
- `bot/states/compose.py` — `ComposeState(StatesGroup)`: `choosing_action`, `choosing_channels`, `waiting_vacancy_text`, `reviewing_variants`, `editing`

**Результат:** UI-компоненты готовы для хендлера.

**Проверка:** импорт без ошибок.

---

### Задача 8.3: Хендлер «Составить текст»

**Файлы:**
- `bot/handlers/compose.py`:
  - Экран выбора: «Сообщение для рассылки» / «Отклик на вакансию» / «Мои шаблоны»
  - Флоу рассылочного сообщения: выбор каналов → генерация → показ вариантов → выбор/переделать/редактировать → сохранить
  - Флоу отклика: ввод текста вакансии → генерация → показ → копировать/переделать
  - Список шаблонов: просмотр, использование, удаление

**Результат:** пользователь генерирует сообщения через LLM, сохраняет шаблоны.

**Проверка:**
- «Составить текст» → «Сообщение для рассылки» → «Все для рассылки» → бот думает → показывает 2–3 варианта
- Выбрать вариант → «Сохранено!»
- «Мои шаблоны» → видит сохранённое сообщение
- «Отклик на вакансию» → ввести текст вакансии → бот генерирует отклик

---

## Фаза 9 — Модуль «Найти заказы»

### Задача 9.1: Regex-фильтр (первый слой)

**Файлы:**
- `parsers/keyword_filter.py` — класс `KeywordFilter`:
  - `__init__(keywords: list[str])` — компилирует regex-паттерны
  - `is_potential_vacancy(text: str) -> bool` — проверяет текст на наличие маркеров вакансии
  - Встроенные паттерны: «ищу», «ищем», «требуется», «вакансия», «нужен», «задача», «проект», «бюджет», «оплата», «фриланс» и т.д.
  - Пользовательские keywords добавляются к встроенным

**Результат:** быстрая предфильтрация без затрат на LLM.

**Проверка:**
```bash
python -c "
from parsers.keyword_filter import KeywordFilter
f = KeywordFilter(['python', 'бот'])
print(f.is_potential_vacancy('Ищу разработчика на python-бота'))  # True
print(f.is_potential_vacancy('Сегодня хорошая погода'))  # False
print(f.is_potential_vacancy('Нужен бот для магазина'))  # True
"
```

---

### Задача 9.2: Сервис парсинга каналов

**Файлы:**
- `services/channel_parser.py` — класс `ChannelParserService`:
  - `parse_channel(channel_id: str) -> int` — парсит последние сообщения из канала (через Bot API), сохраняет в `channel_messages`, возвращает количество новых
  - `parse_user_channels(user_id: str, purpose: str = "monitor") -> int` — парсит все каналы пользователя с нужным purpose

**Ограничение MVP:** работает только для каналов, где бот — участник. Bot API `getUpdates` / `getChat` / forwarded messages.

**Результат:** бот может собирать сообщения из подключённых каналов.

**Проверка:**
- Добавить бота в тестовый канал
- Запустить парсинг этого канала
- В Supabase: `channel_messages` — появились сообщения из канала

---

### Задача 9.3: Сервис фильтрации вакансий

**Файлы:**
- `services/vacancy_filter.py` — класс `VacancyFilterService`:
  - `find_vacancies(user_id: str, limit: int = 10) -> list[dict]`:
    1. Получить каналы пользователя с purpose monitor/both
    2. Получить непроверенные сообщения из `channel_messages`
    3. Слой 1: `KeywordFilter` — отсечь нерелевантные
    4. Слой 2: `LLMClient` + `vacancy_classify` промпт — классифицировать оставшиеся
    5. Пометить результаты в БД (`mark_as_vacancy` / `mark_as_not_vacancy`)
    6. Вернуть вакансии с `vacancy_data`

**Результат:** двухступенчатая фильтрация работает.

**Проверка:**
```bash
python -c "
import asyncio
from services.vacancy_filter import VacancyFilterService
svc = VacancyFilterService()
vacancies = asyncio.run(svc.find_vacancies(user_id='...'))
for v in vacancies:
    print(v['vacancy_data']['title'], v['vacancy_data'].get('budget'))
"
```

---

### Задача 9.4: Клавиатуры и хендлер «Найти заказы»

**Файлы:**
- `bot/keyboards/vacancies.py` — клавиатуры: кнопка поиска, карточки вакансий (пагинация), избранное
- `bot/handlers/vacancies.py`:
  - Экран: «Найти заказы» + «Изменить параметры» + ← Меню
  - Нажатие «Найти» → парсинг каналов → фильтрация → карточки вакансий с пагинацией
  - Карточка: описание, бюджет, канал, дата. Кнопки: «Подготовить отклик» / «В избранное» / «Пропустить»
  - «Подготовить отклик» → вызов `ComposerService.generate_vacancy_response()` → показ текста
  - «Избранное» → список сохранённых вакансий

**Результат:** пользователь ищет вакансии, листает карточки, откликается.

**Проверка:**
- «Найти заказы» → «Найти» → бот думает → «Найдено N вакансий» → карточка 1/N
- Нажать → / ← для навигации
- «Подготовить отклик» → бот генерирует текст
- «В избранное» → «Сохранено»

---

## Фаза 10 — Модуль «Рассылка»

### Задача 10.1: Сервис рассылки

**Файлы:**
- `services/broadcaster.py` — класс `BroadcasterService`:
  - `create_broadcast(user_id: str, message_id: str, channel_ids: list[str]) -> dict` — создаёт рассылку и элементы в БД
  - `send_next_item(broadcast_id: str) -> dict | None` — берёт следующий pending item, уникализирует текст через LLM, отправляет через Bot API, помечает sent/failed
  - `pause(broadcast_id: str) -> None`
  - `resume(broadcast_id: str) -> None`
  - `cancel(broadcast_id: str) -> None`
  - `get_status(broadcast_id: str) -> dict` — текущий статус с прогрессом

Внутри `send_next_item`: проверка тихих часов, проверка лимита в час, уникализация через `rewrite` промпт.

**Результат:** полная логика рассылки, не зависящая от бота.

**Проверка:**
```bash
python -c "
import asyncio
from services.broadcaster import BroadcasterService
svc = BroadcasterService()
bc = asyncio.run(svc.create_broadcast(user_id='...', message_id='...', channel_ids=['...']))
print('Broadcast:', bc['id'], bc['status'])
result = asyncio.run(svc.send_next_item(bc['id']))
print('Sent:', result)
"
```

---

### Задача 10.2: Планировщик рассылки (APScheduler)

**Файлы:**
- `scheduler/jobs.py`:
  - `start_broadcast_job(broadcast_id: str)` — регистрирует interval-задачу в APScheduler: каждые N секунд (рандомная задержка) вызывает `BroadcasterService.send_next_item()`. Останавливается когда нет pending items.
  - `stop_broadcast_job(broadcast_id: str)` — удаляет задачу из планировщика
- Обновить `bot/__main__.py` — инициализация APScheduler при старте бота

**Результат:** рассылка работает в фоне с рандомными задержками.

**Проверка:**
- Создать рассылку на 3 канала
- Запустить job
- В логах: «Sending to @channel_1...», пауза 30–120 сек, «Sending to @channel_2...», пауза, «Sending to @channel_3...»
- В Supabase: broadcast_items — все `status=sent`, broadcast — `status=completed`

---

### Задача 10.3: FSM и клавиатуры рассылки

**Файлы:**
- `bot/keyboards/broadcast.py` — клавиатуры: панель, выбор сообщения, выбор каналов, подтверждение, управление активной рассылкой
- `bot/states/broadcast.py` — `BroadcastState(StatesGroup)`: `choosing_message`, `choosing_channels`, `confirming`

**Результат:** UI-компоненты готовы.

**Проверка:** импорт без ошибок.

---

### Задача 10.4: Хендлер рассылки

**Файлы:**
- `bot/handlers/broadcast.py`:
  - Панель: активная рассылка (если есть) + статус + «Приостановить/Остановить» + «Новая рассылка» + «История»
  - Новая рассылка: выбор сообщения (последнее / из шаблонов / написать новое) → выбор каналов → подтверждение с дисклеймером (если первый раз) → запуск
  - Управление: пауза, возобновление, остановка
  - История рассылок с детализацией

**Результат:** полный флоу рассылки через интерфейс бота.

**Проверка:**
- «Рассылка» → «Новая рассылка» → выбрать шаблон → выбрать каналы → подтвердить
- Панель показывает прогресс «Отправлено 1/3»
- «Приостановить» → рассылка встала → «Возобновить» → продолжила
- «История» → видит завершённую рассылку со статусами

---

## Фаза 11 — Интеграция и финальная сборка

### Задача 11.1: Связать все хендлеры

**Файлы:**
- `bot/handlers/__init__.py` — обновить `register_all_handlers()`: подключить все роутеры (start, menu, profile, settings, radar, compose, vacancies, broadcast)
- `bot/__main__.py` — убедиться что всё инициализируется в правильном порядке: конфиг → БД → мидлвари → хендлеры → планировщик → polling

**Результат:** все модули работают вместе, переходы между экранами корректны.

**Проверка:**
- Пройти полный путь: /start → онбординг → меню → радар → найти каналы → подключить → составить текст → генерация → рассылка → запуск
- Пройти путь: меню → найти заказы → карточки → отклик
- Пройти путь: меню → профиль → редактирование → настройки → изменить лимит

---

### Задача 11.2: Утилиты для текста

**Файлы:**
- `utils/text.py`:
  - `escape_md(text: str) -> str` — экранирование спецсимволов для MarkdownV2
  - `truncate(text: str, max_length: int = 4096) -> str` — обрезка с «...»
  - `format_vacancy_card(vacancy: dict) -> str` — форматирование карточки вакансии
  - `format_channel_card(channel: dict) -> str` — форматирование карточки канала

**Результат:** единообразное форматирование текстов во всём боте.

**Проверка:** юнит-тесты или ручная проверка форматирования.

---

### Задача 11.3: Обработка ошибок

**Файлы:**
- `bot/__main__.py` — глобальный error handler для aiogram:
  - Ловит все необработанные исключения в хендлерах
  - Логирует traceback
  - Отправляет пользователю «Произошла ошибка, попробуй ещё раз»
  - Критические ошибки (БД недоступна, LLM не отвечает) — уведомление админу

**Результат:** бот не падает от необработанных ошибок, пользователь получает понятное сообщение.

**Проверка:**
- Отключить LLM_API_KEY → попробовать генерацию → «Произошла ошибка» (не traceback)
- Вернуть ключ → всё работает

---

### Задача 11.4: Dockerfile

**Файлы:**
- `Dockerfile`:
  - Базовый образ `python:3.11-slim`
  - Копирование и установка requirements.txt
  - Копирование кода
  - CMD: `python -m bot`

**Результат:** проект можно запустить в контейнере.

**Проверка:**
```bash
docker build -t frilobot .
docker run --env-file .env frilobot
# Бот запустился
```

---

### Задача 11.5: README.md

**Файлы:**
- `README.md`:
  - Краткое описание проекта
  - Требования (Python 3.11+, аккаунт Supabase)
  - Инструкция по установке и запуску
  - Переменные окружения
  - Docker-запуск

**Результат:** новый разработчик может развернуть проект по README.

**Проверка:** следуя инструкциям в README, проект запускается с нуля.

---

## Чеклист готовности MVP

- [ ] Бот запускается и отвечает на /start
- [ ] Онбординг: 7 шагов, данные сохраняются
- [ ] Главное меню: 6 кнопок, все ведут в свои модули
- [ ] Профиль: просмотр и редактирование
- [ ] Настройки: просмотр и изменение
- [ ] Радар: поиск каналов через tgstat, подключение, управление
- [ ] Составить текст: генерация рассылочных сообщений, откликов, шаблоны
- [ ] Найти заказы: парсинг → regex → LLM → карточки, избранное, отклики
- [ ] Рассылка: создание, фоновая отправка, пауза, статус, история
- [ ] Ошибки обрабатываются, бот не падает
- [ ] Docker-образ собирается и работает
