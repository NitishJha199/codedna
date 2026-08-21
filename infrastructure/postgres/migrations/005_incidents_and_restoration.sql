BEGIN;

CREATE TABLE incidents (
    id UUID PRIMARY KEY,
    organization_id UUID
        REFERENCES organizations(id),
    service_id UUID
        REFERENCES services(id),
    environment_id UUID
        REFERENCES environments(id),
    deployment_id UUID
        REFERENCES deployments(id),
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    started_at TIMESTAMPTZ NOT NULL,
    detected_at TIMESTAMPTZ,
    mitigated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE INDEX idx_incidents_service_id
    ON incidents(service_id);

CREATE INDEX idx_incidents_environment_id
    ON incidents(environment_id);

CREATE INDEX idx_incidents_deployment_id
    ON incidents(deployment_id);

CREATE INDEX idx_incidents_status
    ON incidents(status);

CREATE INDEX idx_incidents_started_at
    ON incidents(started_at);

CREATE INDEX idx_incidents_resolved_at
    ON incidents(resolved_at);

INSERT INTO schema_migrations (version, name)
VALUES (5, 'incidents_and_restoration');

COMMIT;
