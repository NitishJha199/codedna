BEGIN;

CREATE TABLE schema_migrations (
    version BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, external_id)
);

CREATE TABLE projects (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL
        REFERENCES organizations(id),
    name TEXT NOT NULL,
    provider TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (organization_id, provider, external_id)
);

CREATE TABLE repositories (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL
        REFERENCES projects(id),
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, external_id)
);

CREATE TABLE developers (
    id UUID PRIMARY KEY,
    organization_id UUID
        REFERENCES organizations(id),
    username TEXT,
    display_name TEXT,
    email TEXT,
    provider TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, external_id)
);

CREATE INDEX idx_projects_organization_id
    ON projects(organization_id);

CREATE INDEX idx_repositories_project_id
    ON repositories(project_id);

CREATE INDEX idx_developers_organization_id
    ON developers(organization_id);

INSERT INTO schema_migrations (version, name)
VALUES (1, 'core_identity');

COMMIT;
