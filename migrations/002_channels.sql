-- Миграция 002: channels, user_channels

-- Глобальный справочник каналов
CREATE TABLE IF NOT EXISTS channels (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id       BIGINT UNIQUE,
    username          VARCHAR(255),
    title             VARCHAR(500),
    description       TEXT,
    subscribers_count INTEGER,
    is_paid           BOOLEAN DEFAULT false,
    category          VARCHAR(100),
    source            VARCHAR(50),
    last_parsed_at    TIMESTAMPTZ,
    created_at        TIMESTAMPTZ DEFAULT now()
);

-- Связь пользователя с каналами
CREATE TABLE IF NOT EXISTS user_channels (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id  UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    purpose     VARCHAR(20) NOT NULL,
    is_active   BOOLEAN DEFAULT true,
    created_at  TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_user_channels_user_id ON user_channels(user_id);
CREATE INDEX IF NOT EXISTS idx_user_channels_purpose ON user_channels(user_id, purpose);
