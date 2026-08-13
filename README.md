# CodeDNA

CodeDNA is a DevSecOps correlation platform designed to establish the genealogy of security findings across the software delivery lifecycle.

## Architecture

The approved architecture is documented under `docs/architecture/`.

PostgreSQL is the canonical system of record. Neo4j is the relationship graph projection.

## Project Structure

- `backend/` — FastAPI backend and application services
- `collectors/` — external-system collectors
- `frontend/` — React dashboard
- `graph/` — Neo4j graph projection components
- `infrastructure/` — local and deployment infrastructure definitions
- `docs/` — architecture, decisions, and threat model

## Development Principle

Implementation follows the approved architecture and roadmap. Architectural changes require an ADR.
