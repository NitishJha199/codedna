# CodeDNA Threat Model

## 1. Purpose

This document defines the initial security boundaries and threats for
CodeDNA.

---

## 2. Assets

Primary assets include:

- source-code metadata
- repository metadata
- vulnerability information
- security findings
- CI/CD metadata
- container metadata
- deployment metadata
- service metadata
- organization information
- authentication credentials
- database credentials
- API credentials
- webhook secrets

---

## 3. Trust Boundaries

### External Systems

Examples:

- GitHub
- GitLab
- CI/CD systems
- Kubernetes
- security scanners

External data must be treated as untrusted input.

### Application Boundary

Collectors and APIs validate external data before processing.

### Database Boundary

PostgreSQL and Neo4j are internal infrastructure components and must still be
protected against unauthorized access.

### Frontend Boundary

The React application is an untrusted client of the API.

---

## 4. Initial Threats

### Credential Exposure

Integration credentials could be exposed.

Mitigation:

- environment-based secret injection
- least privilege
- no secrets committed to Git

### Malicious Webhook Payload

An attacker could submit crafted webhook data.

Mitigation:

- webhook authentication
- payload validation
- schema validation

### Data Injection

Malformed external data could attempt to manipulate stored data.

Mitigation:

- parameterized database access
- input validation
- strict schemas

### Unauthorized API Access

An attacker could access sensitive CodeDNA information.

Mitigation:

- authentication
- authorization
- least privilege

### Graph Manipulation

Incorrect graph projection could produce false genealogy.

Mitigation:

- PostgreSQL as source of truth
- deterministic projection
- idempotent graph operations

### Supply Chain Risk

Third-party scanners and dependencies could introduce vulnerabilities.

Mitigation:

- dependency scanning
- container scanning
- pinned dependencies where appropriate

---

## 5. Security Principle

CodeDNA must never treat externally supplied data as trusted merely
because it originated from an integration provider.

All external inputs require validation and controlled processing.
