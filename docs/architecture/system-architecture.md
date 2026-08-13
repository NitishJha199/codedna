# CodeDNA System Architecture

## 1. Purpose

CodeDNA is a DevSecOps correlation platform designed to establish the
genealogy of security findings across the software delivery lifecycle.

The primary architectural objective is to answer:

> How did a security issue travel from source code to production,
> and what is its current blast radius?

---

## 2. High-Level Architecture

```text
Developer
    |
    v
GitHub / GitLab
    |
    v
Collectors
    |
    v
Event Processor
    |
    +--------------------+
    |                    |
    v                    v
PostgreSQL            Neo4j
    |                    ^
    |                    |
    +--> Graph Projection+
    |
    v
Correlation Engine
    |
    v
Risk Engine
    |
    v
FastAPI
    |
    v
React Dashboard

---

## 3. Components

### Collectors

Collectors retrieve information from external systems.

Initial collector responsibilities:

- Git repositories
- Dependencies
- Security findings
- CI/CD builds
- Container images
- SBOMs
- Deployments

Collectors do not perform complex correlation or risk calculations.

### Event Processor

The Event Processor:

- validates incoming events
- normalizes provider-specific data
- deduplicates events
- enriches data where appropriate
- persists normalized records

### PostgreSQL

PostgreSQL is the authoritative system of record.

It stores canonical CodeDNA entities and ingestion events.

### Neo4j

Neo4j is the relationship graph.

It represents relationships between canonical entities and supports
genealogy and blast-radius traversal.

### Correlation Engine

The Correlation Engine establishes relationships across:

- source code
- dependencies
- vulnerabilities
- builds
- artifacts
- container images
- deployments
- services
- environments

### Risk Engine

The Risk Engine determines contextual risk using factors such as:

- vulnerability severity
- exploitability
- production exposure
- asset criticality
- deployment context
- vulnerability age

### FastAPI

FastAPI provides the application API.

The frontend does not directly access PostgreSQL or Neo4j.

### React

React provides the CodeDNA dashboard and investigation interface.

---

## 4. Architectural Boundaries

### Collector != Correlation

Collectors collect facts.

Correlation establishes relationships.

### Correlation != Risk

Correlation determines how entities are connected.

Risk determines their security priority.

### PostgreSQL != Neo4j

PostgreSQL is the system of record.

Neo4j is the relationship projection.

### Backend != Frontend

The backend owns business logic.

The frontend presents backend results.

### Scanner != CodeDNA

Security scanners discover security information.

CodeDNA correlates and contextualizes that information.

---

## 5. Core Data Flow

```text
External System
      |
      v
Collector
      |
      v
Raw Event
      |
      v
Event Processor
      |
      +------> PostgreSQL
      |
      v
Graph Projection
      |
      v
Neo4j
      |
      v
Correlation Engine
      |
      v
Risk Engine
      |
      v
FastAPI
      |
      v
React
```

---

## 6. Security Genealogy

The core CodeDNA relationship chain is:

```text
Vulnerability
      |
      v
Dependency
      |
      v
Repository
      |
      v
Commit
      |
      v
Build
      |
      v
Artifact
      |
      v
Container Image
      |
      v
Deployment
      |
      v
Environment
      |
      v
Service
```

This chain enables CodeDNA to determine where a vulnerability is actually deployed.

---

## 7. Architectural Constraints

The initial architecture intentionally does not include:

- Kafka
- Redis
- Elasticsearch
- Kubernetes as an internal CodeDNA dependency
- additional databases
- additional message brokers

Any addition requires an explicit architecture revision.

### Secret Handling

Secrets and credentials must never be committed to source control.

Integration credentials are supplied at runtime through environment or deployment configuration.

CodeDNA must follow least-privilege principles for external integrations.

No dedicated external secrets-management service is required for the initial implementation.

---

## 8. Infrastructure

Initial deployment target:

- AWS EC2
- Ubuntu 24.04 LTS
- Docker Engine
- Docker Compose

Application components will be containerized where appropriate.

---

## 9. Architecture Principle

The system prioritizes traceability and explainability.

A CodeDNA risk result should be explainable through the underlying relationships that produced it.

---

## 10. Architecture Change Policy

The architecture defined by this document is the baseline implementation architecture.

New infrastructure components, databases, message brokers, major frameworks, or architectural patterns must not be introduced implicitly.

Any required architectural change must be:

1. identified
2. justified
3. documented
4. reviewed
5. recorded as an Architecture Decision Record (ADR)

Implementation should follow the approved architecture rather than evolve it opportunistically.
