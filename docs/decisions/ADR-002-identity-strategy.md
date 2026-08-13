# ADR-002: Identity Strategy

## Status

Accepted

## Decision

CodeDNA will use UUID v4 internal identifiers for canonical entities.

External provider identifiers are stored separately.

## Rationale

Provider identifiers are not guaranteed to be globally consistent across
systems.

Internal UUIDs provide stable CodeDNA identity while external IDs retain
provider correlation.

## Consequences

Every integration must map external identities to CodeDNA identities.
