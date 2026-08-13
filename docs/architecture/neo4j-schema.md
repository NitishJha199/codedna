# CodeDNA Neo4j Graph Schema

## 1. Purpose

Neo4j represents the relationship and genealogy layer of CodeDNA.

It provides graph traversal capabilities for genealogy and blast-radius analysis.
---

## 2. Node Types

Initial node labels:

- Organization
- Project
- Repository
- Developer
- Commit
- PullRequest
- Dependency
- Vulnerability
- Finding
- Pipeline
- Build
- Artifact
- ContainerImage
- SBOM
- Environment
- Service
- Deployment
---

## 3. Node Identity

Every node contains the corresponding PostgreSQL entity UUID.

Example:

Repository
{
    id
    name
    provider
}

The PostgreSQL UUID is the stable identity used for graph projection.
---

## 4. Relationship Types

Initial relationship types include:

- CONTAINS
- OWNS
- CONTRIBUTED_TO
- CREATED
- MODIFIES
- DEPENDS_ON
- AFFECTED_BY
- PRODUCED
- CONTAINS_ARTIFACT
- DERIVED_FROM
- DEPLOYED_TO
- RUNS_IN
- SERVES
- TARGETS
---

## 5. Projection Model

Neo4j is a projection of PostgreSQL canonical state.

Graph writes must be deterministic and idempotent.

A graph projection can be recreated from PostgreSQL data.
---

## 6. Projection Rules

Canonical PostgreSQL entities are projected into corresponding Neo4j nodes.

Canonical PostgreSQL relationships are projected into corresponding Neo4j relationships.

Projection operations must use stable entity identifiers.

Repeated projection of the same entity must not create duplicate nodes or relationships.
---

## 7. Genealogy Traversal

The graph must support traversal across the software delivery lifecycle.

A primary genealogy path is:

Vulnerability -> Dependency -> Repository -> Commit -> Build -> Artifact -> ContainerImage -> Deployment -> Environment -> Service

This traversal supports investigation of where a security issue can propagate.
---

## 8. Blast Radius

Neo4j must support traversal from a security finding toward affected downstream assets.

Example traversal targets include:

- affected repositories
- affected builds
- affected artifacts
- affected container images
- affected deployments
- affected environments
- affected services
---

## 9. Consistency

PostgreSQL remains authoritative if Neo4j becomes unavailable.

Projection failures must be retryable.

The graph must not introduce canonical information that cannot be traced back to PostgreSQL.
---

## 10. Design Principle

Neo4j exists to make CodeDNA relationships efficiently traversable.

It is not an independent system of record.
