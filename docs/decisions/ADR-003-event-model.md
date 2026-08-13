# ADR-003: Event Model

## Status

Accepted

## Decision

All externally received information will enter CodeDNA through a
normalized event model with idempotency protection.

## Rationale

External systems can retry events and may deliver events out of order.

An explicit event model provides:

- auditability
- deduplication
- retry capability
- debugging
- future replay capability

## Consequences

Events require stable idempotency keys and timestamps representing both
source occurrence and CodeDNA receipt.
