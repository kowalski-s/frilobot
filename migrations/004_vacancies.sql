-- Миграция 004: channel_messages, saved_vacancies

-- Сообщения из каналов (для поиска вакансий)
CREATE TABLE IF NOT EXISTS channel_messages (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id           UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    telegram_message_id  BIGINT NOT NULL,
    text                 TEXT,
    date                 TIMESTAMPTZ,
    is_vacancy           BOOLEAN,
    vacancy_data         JSONB,
    created_at           TIMESTAMPTZ DEFAULT now(),
    UNIQUE(channel_id, telegram_message_id)
);

CREATE INDEX IF NOT EXISTS idx_channel_messages_channel_id ON channel_messages(channel_id);
CREATE INDEX IF NOT EXISTS idx_channel_messages_date ON channel_messages(date DESC);
CREATE INDEX IF NOT EXISTS idx_channel_messages_vacancy ON channel_messages(is_vacancy) WHERE is_vacancy = true;

-- Сохранённые вакансии (избранное)
CREATE TABLE IF NOT EXISTS saved_vacancies (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_message_id  UUID NOT NULL REFERENCES channel_messages(id) ON DELETE CASCADE,
    status              VARCHAR(20) DEFAULT 'saved',
    response_text       TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);
