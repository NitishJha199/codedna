# CodeDNA Data Architecture

## 1. Purpose

This document defines the ownership and flow of CodeDNA data.

---

## 2. Database Responsibilities

CodeDNA uses two primary databases.

### PostgreSQL

PostgreSQL is the canonical system of record.

It owns:

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

### Neo4j

Neo4j is the relationship graph.

It stores graph projections of canonical PostgreSQL entities and their relationships.
---

## 3. Source of Truth

PostgreSQL is authoritative for canonical CodeDNA data.

Neo4j is a derived relationship projection.

The relationship is:

PostgreSQL
    |
    | Graph Projection
    v
Neo4j

If Neo4j is lost or becomes inconsistent, it can be rebuilt from PostgreSQL.
---

## 4. Data Flow

External systems provide information through collectors.

The normalized flow is:

External System -> Collector -> Event Processor -> PostgreSQL -> Graph Projection -> Neo4j

Correlation and risk analysis operate on the canonical data and graph relationships.
---

## 5. Event Data

All externally received information enters CodeDNA through the normalized event model.

Events provide:

- auditability
- deduplication
- retry capability
- debugging
- replay capability

Events contain both source occurrence time and CodeDNA receipt time where available.
---

## 6. Canonical Data

Canonical records are maintained in PostgreSQL.

Examples include:

- repositories
- commits
- dependencies
- vulnerabilities
- findings
- builds
- artifacts
- deployments
- services
- environments

These records provide the authoritative state from which downstream projections are generated.
---

## 7. Graph Projection

Neo4j receives projections of canonical PostgreSQL entities and relationships.

Projection operations must be:

- deterministic
- idempotent
- retryable

Graph projection failures must not invalidate PostgreSQL transactions.
---

## 8. Data Lifecycle

CodeDNA data follows the lifecycle:

Ingestion -> Normalization -> Persistence -> Projection -> Correlation -> Risk Analysis -> API -> Dashboard

Each stage has a defined responsibility and must not silently assume ownership belonging to another stage.
---

## 9. Data Integrity

External data is considered untrusted until validated and normalized.

Canonical data must satisfy database constraints and application validation.

Graph relationships must be traceable to canonical PostgreSQL records.
---

## 10. Design Principle

PostgreSQL owns canonical state.

Neo4j owns the relationship projection.

The architecture prioritizes traceability, reproducibility, and explainability.
