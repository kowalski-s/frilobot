-- Миграция 001: users, settings, search_profiles

-- Расширение для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id     BIGINT UNIQUE NOT NULL,
    username        VARCHAR(255),
    first_name      VARCHAR(255),
    specializations TEXT[],
    services_description TEXT,
    portfolio_url   VARCHAR(500),
    onboarding_completed BOOLEAN DEFAULT false,
    disclaimer_accepted  BOOLEAN DEFAULT false,
    is_admin        BOOLEAN DEFAULT false,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- Таблица настроек пользователя
CREATE TABLE IF NOT EXISTS settings (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    broadcast_limit_per_hour INTEGER DEFAULT 5,
    quiet_hours_start       TIME DEFAULT '23:00',
    quiet_hours_end         TIME DEFAULT '08:00',
    min_delay_seconds       INTEGER DEFAULT 30,
    max_delay_seconds       INTEGER DEFAULT 120,
    updated_at              TIMESTAMPTZ DEFAULT now()
);

-- Профили поиска вакансий
CREATE TABLE IF NOT EXISTS search_profiles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keywords    TEXT[],
    min_budget  INTEGER,
    work_format TEXT[],
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT now()
);
