



# ADR-001: Database Responsibilities

## Status

Accepted

## Decision

CodeDNA will use PostgreSQL as the authoritative system of record and
Neo4j as the relationship graph projection.

## Rationale

PostgreSQL provides strong transactional consistency and is well suited
to canonical application records.

Neo4j provides efficient graph traversal for genealogy and blast-radius
analysis.

Separating responsibilities avoids forcing either database to perform
the other's primary role.

## Consequences

- PostgreSQL is authoritative.
- Neo4j can be rebuilt from PostgreSQL.
- Graph projection must be reliable and retryable.
