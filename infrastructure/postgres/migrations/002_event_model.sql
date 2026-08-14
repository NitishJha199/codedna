BEGIN;

CREATE TABLE events (
    id UUID PRIMARY KEY,
    provider TEXT NOT NULL,
    event_type TEXT NOT NULL,
    external_event_id TEXT,
    idempotency_key TEXT NOT NULL,
    source_occurred_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL,
    processing_status TEXT NOT NULL DEFAULT 'pending',
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (idempotency_key)
);

CREATE INDEX idx_events_provider
    ON events(provider);

CREATE INDEX idx_events_type
    ON events(event_type);

CREATE INDEX idx_events_status
    ON events(processing_status);

CREATE INDEX idx_events_source_occurred_at
    ON events(source_occurred_at);

CREATE INDEX idx_events_external_id
    ON events(provider, external_event_id);

INSERT INTO schema_migrations (version, name)
VALUES (2, 'event_model');

COMMIT;
