BEGIN;

CREATE TABLE commits (
    id UUID PRIMARY KEY,
    repository_id UUID NOT NULL
        REFERENCES repositories(id),
    developer_id UUID
        REFERENCES developers(id),
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    sha TEXT NOT NULL,
    message TEXT,
    occurred_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id),
    UNIQUE (repository_id, sha)
);

CREATE TABLE pull_requests (
    id UUID PRIMARY KEY,
    repository_id UUID NOT NULL
        REFERENCES repositories(id),
    author_id UUID
        REFERENCES developers(id),
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    number BIGINT,
    title TEXT,
    state TEXT NOT NULL DEFAULT 'open',
    source_branch TEXT,
    target_branch TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id),
    UNIQUE (repository_id, number)
);

CREATE TABLE dependencies (
    id UUID PRIMARY KEY,
    repository_id UUID NOT NULL
        REFERENCES repositories(id),
    name TEXT NOT NULL,
    version TEXT,
    package_manager TEXT,
    provider TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (repository_id, name, version, package_manager)
);

CREATE TABLE vulnerabilities (
    id UUID PRIMARY KEY,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    identifier TEXT NOT NULL,
    severity TEXT,
    summary TEXT,
    description TEXT,
    published_at TIMESTAMPTZ,
    modified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id),
    UNIQUE (identifier)
);

CREATE TABLE security_findings (
    id UUID PRIMARY KEY,
    repository_id UUID NOT NULL
        REFERENCES repositories(id),
    dependency_id UUID
        REFERENCES dependencies(id),
    vulnerability_id UUID
        REFERENCES vulnerabilities(id),
    provider TEXT NOT NULL,
    external_id TEXT,
    finding_type TEXT NOT NULL,
    severity TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    title TEXT,
    description TEXT,
    detected_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (provider, external_id)
);

CREATE INDEX idx_commits_repository_id
    ON commits(repository_id);

CREATE INDEX idx_commits_developer_id
    ON commits(developer_id);

CREATE INDEX idx_commits_occurred_at
    ON commits(occurred_at);

CREATE INDEX idx_pull_requests_repository_id
    ON pull_requests(repository_id);

CREATE INDEX idx_pull_requests_author_id
    ON pull_requests(author_id);

CREATE INDEX idx_pull_requests_state
    ON pull_requests(state);

CREATE INDEX idx_dependencies_repository_id
    ON dependencies(repository_id);

CREATE INDEX idx_dependencies_name
    ON dependencies(name);

CREATE INDEX idx_vulnerabilities_severity
    ON vulnerabilities(severity);

CREATE INDEX idx_security_findings_repository_id
    ON security_findings(repository_id);

CREATE INDEX idx_security_findings_dependency_id
    ON security_findings(dependency_id);

CREATE INDEX idx_security_findings_vulnerability_id
    ON security_findings(vulnerability_id);

CREATE INDEX idx_security_findings_status
    ON security_findings(status);

CREATE INDEX idx_security_findings_severity
    ON security_findings(severity);

INSERT INTO schema_migrations (version, name)
VALUES (3, 'source_and_security');

COMMIT;
