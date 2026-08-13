# CodeDNA PostgreSQL Schema

## 1. Purpose

PostgreSQL is the authoritative system of record for CodeDNA.
---

## 2. Common Conventions

Primary entity identifiers:

UUID v4

External provider identifiers are stored separately from internal CodeDNA identifiers.

All timestamps use UTC.

Database records maintain created and updated timestamps where appropriate.
---

## 3. Core Entities

The initial PostgreSQL model contains the following canonical entities:

- organizations
- projects
- repositories
- developers
- commits
- pull requests
- dependencies
- vulnerabilities
- security findings
- pipelines
- builds
- artifacts
- container images
- SBOMs
- environments
- services
- deployments
- events
---

## 4. Identity

Each canonical entity receives a CodeDNA UUID.

External identifiers are retained for provider correlation.

Provider-specific identifiers must not become the primary identity of CodeDNA entities.
---

## 5. Event Storage

Events are stored as immutable ingestion records.

Each event contains, where applicable:

- event identifier
- provider
- event type
- external event identifier
- source occurrence timestamp
- CodeDNA receipt timestamp
- normalized payload
- processing status

Event processing must be idempotent.
---

## 6. Relationship Ownership

PostgreSQL stores canonical relationships between entities.

Examples include:

- project to repository
- repository to developer
- repository to commit
- commit to pull request
- dependency to vulnerability
- pipeline to build
- build to artifact
- artifact to container image
- deployment to environment
- deployment to service

These relationships form the canonical basis for Neo4j graph projection.
---

## 7. Data Integrity

Database constraints should enforce:

- primary-key uniqueness
- required relationships
- foreign-key integrity
- appropriate uniqueness for external identifiers
- valid lifecycle states

Application-level validation does not replace database integrity.
---

## 8. Graph Projection

PostgreSQL remains authoritative when Neo4j projection fails.

A failed graph projection must be retryable.

Neo4j must be reconstructable from PostgreSQL data.
---

## 9. Security

Database credentials must never be stored in source control.

Database access must use least privilege.

Application components should receive only the database permissions required for their responsibilities.
---

## 10. Schema Evolution

Schema changes must be introduced through versioned database migrations.

Migration history must be maintained in source control.

Destructive schema changes require explicit review.
---

## 11. Design Principle

PostgreSQL owns canonical CodeDNA state.

Neo4j consumes a projection of that state for relationship traversal.

No application component should treat Neo4j as the authoritative source for canonical entity data.
