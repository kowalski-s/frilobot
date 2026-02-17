-- Миграция 003: messages, broadcasts, broadcast_items

-- Сообщения (шаблоны рассылки, отклики)
CREATE TABLE IF NOT EXISTS messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(20),
    content     TEXT NOT NULL,
    is_template BOOLEAN DEFAULT false,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_user_templates ON messages(user_id) WHERE is_template = true;

-- Рассылки
CREATE TABLE IF NOT EXISTS broadcasts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id      UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    status          VARCHAR(20) DEFAULT 'pending',
    total_channels  INTEGER DEFAULT 0,
    sent_count      INTEGER DEFAULT 0,
    error_count     INTEGER DEFAULT 0,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_broadcasts_user_id ON broadcasts(user_id);
CREATE INDEX IF NOT EXISTS idx_broadcasts_status ON broadcasts(status);

-- Элементы рассылки (одно сообщение → один канал)
CREATE TABLE IF NOT EXISTS broadcast_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    broadcast_id    UUID NOT NULL REFERENCES broadcasts(id) ON DELETE CASCADE,
    user_channel_id UUID NOT NULL REFERENCES user_channels(id) ON DELETE CASCADE,
    status          VARCHAR(20) DEFAULT 'pending',
    sent_at         TIMESTAMPTZ,
    error_message   TEXT,
    unique_content  TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_broadcast_items_broadcast_id ON broadcast_items(broadcast_id);
CREATE INDEX IF NOT EXISTS idx_broadcast_items_status ON broadcast_items(status);
