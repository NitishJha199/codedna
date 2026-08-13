# ADR-004: Graph Projection

## Status

Accepted

## Decision

Neo4j will be maintained as a projection of PostgreSQL rather than as an
independent source of truth.

## Rationale

This allows the graph to be rebuilt if necessary and keeps transactional
ownership unambiguous.

## Consequences

Graph projection failures must be retryable.

PostgreSQL transactions do not depend on successful Neo4j writes.
