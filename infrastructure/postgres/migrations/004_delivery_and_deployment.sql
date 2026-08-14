BEGIN;

CREATE TABLE pipelines (
    id UUID PRIMARY KEY,
    repository_id UUID NOT NULL
        REFERENCES repositories(id),
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    name TEXT,
    status TEXT,
    branch TEXT,
    commit_id UUID
        REFERENCES commits(id),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE TABLE builds (
    id UUID PRIMARY KEY,
    pipeline_id UUID NOT NULL
        REFERENCES pipelines(id),
    commit_id UUID
        REFERENCES commits(id),
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    status TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    build_id UUID
        REFERENCES builds(id),
    repository_id UUID
        REFERENCES repositories(id),
    provider TEXT,
    external_id TEXT,
    name TEXT NOT NULL,
    version TEXT,
    artifact_type TEXT,
    digest TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE TABLE container_images (
    id UUID PRIMARY KEY,
    artifact_id UUID
        REFERENCES artifacts(id),
    repository_id UUID
        REFERENCES repositories(id),
    registry TEXT NOT NULL,
    image_name TEXT NOT NULL,
    tag TEXT,
    digest TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (registry, image_name, digest)
);

CREATE TABLE sboms (
    id UUID PRIMARY KEY,
    artifact_id UUID
        REFERENCES artifacts(id),
    container_image_id UUID
        REFERENCES container_images(id),
    format TEXT NOT NULL,
    version TEXT,
    digest TEXT,
    generated_at TIMESTAMPTZ,
    payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE environments (
    id UUID PRIMARY KEY,
    organization_id UUID
        REFERENCES organizations(id),
    name TEXT NOT NULL,
    environment_type TEXT,
    provider TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE TABLE services (
    id UUID PRIMARY KEY,
    organization_id UUID
        REFERENCES organizations(id),
    name TEXT NOT NULL,
    provider TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE TABLE deployments (
    id UUID PRIMARY KEY,
    environment_id UUID NOT NULL
        REFERENCES environments(id),
    service_id UUID NOT NULL
        REFERENCES services(id),
    artifact_id UUID
        REFERENCES artifacts(id),
    container_image_id UUID
        REFERENCES container_images(id),
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    status TEXT,
    deployed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE INDEX idx_pipelines_repository_id
    ON pipelines(repository_id);

CREATE INDEX idx_pipelines_commit_id
    ON pipelines(commit_id);

CREATE INDEX idx_pipelines_status
    ON pipelines(status);

CREATE INDEX idx_builds_pipeline_id
    ON builds(pipeline_id);

CREATE INDEX idx_builds_commit_id
    ON builds(commit_id);

CREATE INDEX idx_builds_status
    ON builds(status);

CREATE INDEX idx_artifacts_build_id
    ON artifacts(build_id);

CREATE INDEX idx_artifacts_repository_id
    ON artifacts(repository_id);

CREATE INDEX idx_artifacts_digest
    ON artifacts(digest);

CREATE INDEX idx_container_images_artifact_id
    ON container_images(artifact_id);

CREATE INDEX idx_container_images_repository_id
    ON container_images(repository_id);

CREATE INDEX idx_container_images_digest
    ON container_images(digest);

CREATE INDEX idx_sboms_artifact_id
    ON sboms(artifact_id);

CREATE INDEX idx_sboms_container_image_id
    ON sboms(container_image_id);

CREATE INDEX idx_environments_organization_id
    ON environments(organization_id);

CREATE INDEX idx_services_organization_id
    ON services(organization_id);

CREATE INDEX idx_deployments_environment_id
    ON deployments(environment_id);

CREATE INDEX idx_deployments_service_id
    ON deployments(service_id);

CREATE INDEX idx_deployments_artifact_id
    ON deployments(artifact_id);

CREATE INDEX idx_deployments_container_image_id
    ON deployments(container_image_id);

CREATE INDEX idx_deployments_status
    ON deployments(status);

CREATE INDEX idx_deployments_deployed_at
    ON deployments(deployed_at);

INSERT INTO schema_migrations (version, name)
VALUES (4, 'delivery_and_deployment');

COMMIT;
