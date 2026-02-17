# Frilo — CLAUDE.md

## Проект

Frilo — Telegram-бот (SaaS, мультитенант) для фрилансеров. Ищет каналы по нише, генерирует продающие сообщения через LLM, рассылает их с безопасной частотой, мониторит вакансии и помогает откликаться. Полная документация — `PRD.md`.

## Статус

Этап 1 — Фундамент. Фаза 4 завершена. Переход к Фазе 5.

### Что сделано
- Фаза 1: структура проекта, конфиг, точка входа
- Фаза 2.1: db/connection.py — singleton-клиент Supabase
- Фаза 2.2–2.5: SQL-миграции применены в Supabase через MCP — 10 таблиц
- Фаза 2.6–2.12: все 7 репозиториев (users, settings, channels, messages, broadcasts, vacancies, search_profiles) — проверены на живой БД
- Фаза 3.1: bot/middlewares/auth.py — AuthMiddleware (авторегистрация, data["user"])
- Фаза 3.2: bot/middlewares/throttling.py — ThrottlingMiddleware (1 msg/sec)
- Фаза 3.3: bot/filters/admin.py — IsAdmin (фильтр по ADMIN_IDS и is_admin)
- Фаза 3.4: bot/callbacks/pagination.py — MenuCallback, PageCallback
- Фаза 3.5: bot/keyboards/menu.py — клавиатура главного меню (6 кнопок)
- Фаза 3.6: bot/handlers/start.py, menu.py, __init__.py — /start, меню с заглушками, подключение мидлварей в __main__.py
- Фаза 3.7: bot/states/onboarding.py, bot/keyboards/onboarding.py — FSM (7 состояний), клавиатуры (мультивыбор, бюджет, формат, дисклеймер)
- Фаза 3.8: bot/handlers/start.py — полный онбординг 7 шагов с сохранением в users + search_profiles
- Фаза 4.1: bot/keyboards/profile.py — ProfileCallback, клавиатуры профиля (3 кнопки редактирования + возврат)
- Фаза 4.2: bot/states/profile.py — ProfileEditState (6 состояний), bot/handlers/profile.py — просмотр профиля, редактирование специализаций/описания/параметров поиска через FSM

### Что дальше
- Фаза 5: модуль «Настройки» (просмотр и изменение лимитов рассылки, тихих часов)

## Технический стек

| Компонент | MVP | Продакшен |
|-----------|-----|-----------|
| Язык | Python 3.11+ | — |
| Telegram Bot | aiogram 3 | — |
| Userbot | — (не на MVP) | Telethon |
| LLM | Определим позже | — |
| БД | Supabase Cloud (supabase-py) | PostgreSQL на VPS (asyncpg) |
| Планировщик | APScheduler (asyncio) | Celery + Redis (если нужно) |
| HTTP-клиент | aiohttp | — |
| Парсинг HTML | BeautifulSoup4 | — |
| Хостинг | Локально / Render.com | VPS Timeweb / Selectel |

## Структура проекта

```
frilobot/
├── bot/                        # Telegram Bot (aiogram 3) — только UI-слой
│   ├── __main__.py             # Точка входа
│   ├── config.py               # Настройки из .env
│   ├── handlers/               # Хендлеры по модулям
│   │   ├── start.py            #   /start, онбординг
│   │   ├── menu.py             #   Главное меню
│   │   ├── radar.py            #   Радар (поиск каналов)
│   │   ├── compose.py          #   Составить текст
│   │   ├── vacancies.py        #   Найти заказы
│   │   ├── broadcast.py        #   Рассылка
│   │   ├── profile.py          #   Мой профиль
│   │   └── settings.py         #   Настройки
│   ├── keyboards/              # Inline/reply клавиатуры (по модулям)
│   ├── states/                 # FSM-состояния (онбординг, compose, broadcast)
│   ├── middlewares/             # auth.py, throttling.py
│   ├── filters/                # admin.py
│   └── callbacks/              # Callback data factories, пагинация
│
├── services/                   # Бизнес-логика (НЕ зависит от aiogram)
│   ├── radar.py                # Поиск каналов
│   ├── composer.py             # Генерация текстов через LLM
│   ├── vacancy_filter.py       # Двухступенчатая фильтрация вакансий
│   ├── broadcaster.py          # Логика рассылки
│   └── channel_parser.py       # Парсинг сообщений из каналов
│
├── llm/                        # Интеграция с LLM
│   ├── client.py               # Абстракция клиента (смена провайдера = замена этого файла)
│   └── prompts/                # Промпты: broadcast_message, vacancy_response, vacancy_classify, rewrite
│
├── db/                         # Работа с БД
│   ├── connection.py           # Подключение (supabase-py на MVP → asyncpg на проде)
│   └── repositories/           # Repository pattern: users, channels, messages, broadcasts, vacancies, settings
│
├── scheduler/                  # APScheduler — задачи рассылки, парсинга
│   └── jobs.py
│
├── parsers/                    # Парсеры внешних источников
│   ├── tgstat.py               # Парсер tgstat.ru
│   └── keyword_filter.py       # Regex-фильтр (первый слой перед LLM)
│
├── userbot/                    # Telethon (пустой на MVP)
├── utils/                      # Утилиты (text.py и т.д.)
├── migrations/                 # SQL-миграции
│
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### Принцип слоёв

```
Telegram → bot/handlers → services → db/repositories → PostgreSQL
                              ↓
                          llm/client → LLM API
                              ↓
                         parsers/ → tgstat / regex
```

- `bot/` — только Telegram UI. Не обращается к БД напрямую, не содержит бизнес-логику.
- `services/` — бизнес-логика. Не знает про aiogram. Вызывается из хендлеров, тестов, CLI.
- `db/repositories/` — изолирует SQL. При смене драйвера меняется только `connection.py` и внутренности репозиториев.
- `llm/` — абстракция над LLM. Промпты отдельно, клиент отдельно.

## Команды

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python -m bot

# Переменные окружения
cp .env.example .env
# Заполнить .env перед запуском
```

## Переменные окружения

```
BOT_TOKEN           — токен бота от @BotFather
ADMIN_IDS           — Telegram ID админов через запятую
SUPABASE_URL        — URL проекта Supabase
SUPABASE_KEY        — anon/service_role key
LLM_API_KEY         — API-ключ LLM
LLM_MODEL           — название модели
```

## Правила разработки

### Язык кода
- **Переменные, функции, классы** — на английском (`user_channels`, `BroadcastService`, `get_active_broadcasts`)
- **Комментарии в коде** — на русском (`# Проверяем, прошёл ли пользователь онбординг`)
- **Docstring** — на русском (`"""Возвращает список каналов пользователя для рассылки."""`)
- **Commit-сообщения** — на русском
- **Логирование** — на английском (для совместимости с мониторингом)

### Архитектура
- Хендлер НЕ обращается к БД напрямую — только через `services/`
- Сервис НЕ импортирует aiogram — только чистая логика
- Репозиторий НЕ содержит бизнес-логику — только CRUD
- Новый модуль бота = новый файл в `handlers/`, `keyboards/`, `states/`. Существующие файлы не трогаем.

### Стиль
- Асинхронный код везде (`async/await`)
- Типизация: type hints обязательны для аргументов функций и возвращаемых значений
- Форматирование: ruff (или black + isort)
- Линтинг: ruff
- Нет `*` импортов. Только явные.

### БД
- Все таблицы и их поля описаны в `PRD.md`, раздел 6
- UUID как первичный ключ
- `created_at` / `updated_at` — TIMESTAMPTZ
- Изоляция данных по `user_id` (мультитенант)

### Безопасность
- `.env` в `.gitignore`
- Секреты только через переменные окружения
- Валидация пользовательского ввода на уровне хендлеров
- SQL-инъекции предотвращены параметризованными запросами

## Этапы разработки

1. **Фундамент** — структура, конфиг, БД, /start, онбординг, главное меню ← ТЕКУЩИЙ
2. **Составить текст** — LLM-интеграция, генерация сообщений, шаблоны
3. **Радар** — парсер tgstat, ручной ввод каналов, управление
4. **Найти заказы** — парсинг каналов, regex + LLM фильтрация, карточки
5. **Рассылка** — очередь, APScheduler, уникализация, статусы
6. **Userbot** — Telethon, авторизация, рассылка от имени пользователя
7. **Монетизация** — тарифы, платежи, лимиты

## Четыре модуля бота

| Модуль | Описание | Хендлер |
|--------|----------|---------|
| Радар | Поиск каналов/чатов по нише | `handlers/radar.py` |
| Составить текст | LLM-генерация сообщений для рассылки и откликов | `handlers/compose.py` |
| Найти заказы | Мониторинг вакансий (regex + LLM фильтрация) | `handlers/vacancies.py` |
| Рассылка | Автоотправка по каналам с безопасной частотой | `handlers/broadcast.py` |
