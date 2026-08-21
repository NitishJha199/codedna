from typing import Any
from backend.app.graph.neo4j import get_driver


def get_deployment_lineage(deployment_id: str) -> dict[str, Any] | None:
    query = """
    MATCH (d:Deployment {id: $deployment_id})
    OPTIONAL MATCH (d)-[:DEPLOYED_TO]->(env:Environment)
    OPTIONAL MATCH (d)-[:DEPLOYS]->(svc:Service)
    OPTIONAL MATCH (art:Artifact)-[:HAS_DEPLOYMENT]->(d)
    OPTIONAL MATCH (b:Build)-[:PRODUCES]->(art)
    OPTIONAL MATCH (p:Pipeline)-[:HAS_BUILD]->(b)
    OPTIONAL MATCH (repo:Repository)-[:HAS_PIPELINE]->(p)
    OPTIONAL MATCH (b)-[:BUILDS_FROM]->(c:Commit)
    OPTIONAL MATCH (c)-[:AUTHORED_BY]->(dev:Developer)
    RETURN 
        {
            id: d.id,
            status: d.status,
            external_id: d.external_id,
            deployed_at: toString(d.deployed_at)
        } AS deployment,
        CASE WHEN env IS NOT NULL THEN {
            id: env.id,
            name: env.name,
            environment_type: env.environment_type
        } ELSE null END AS environment,
        CASE WHEN svc IS NOT NULL THEN {
            id: svc.id,
            name: svc.name
        } ELSE null END AS service,
        CASE WHEN art IS NOT NULL THEN {
            id: art.id,
            name: art.name,
            version: art.version,
            artifact_type: art.artifact_type
        } ELSE null END AS artifact,
        CASE WHEN b IS NOT NULL THEN {
            id: b.id,
            status: b.status,
            external_id: b.external_id
        } ELSE null END AS build,
        CASE WHEN p IS NOT NULL THEN {
            id: p.id,
            name: p.name,
            provider: p.provider
        } ELSE null END AS pipeline,
        CASE WHEN repo IS NOT NULL THEN {
            id: repo.id,
            name: repo.name
        } ELSE null END AS repository,
        CASE WHEN c IS NOT NULL THEN {
            id: c.id,
            sha: c.sha,
            message: c.message
        } ELSE null END AS commit,
        CASE WHEN dev IS NOT NULL THEN {
            id: dev.id,
            username: dev.username,
            display_name: dev.display_name,
            email: dev.email
        } ELSE null END AS developer
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(query, deployment_id=deployment_id)
            record = result.single()
            if not record or not record["deployment"]:
                return None
            return {
                "deployment": record["deployment"],
                "environment": record["environment"],
                "service": record["service"],
                "artifact": record["artifact"],
                "build": record["build"],
                "pipeline": record["pipeline"],
                "repository": record["repository"],
                "commit": record["commit"],
                "developer": record["developer"],
            }
    finally:
        driver.close()


def get_vulnerability_impact(vulnerability_id: str) -> dict[str, Any] | None:
    query = """
    MATCH (v:Vulnerability {id: $vulnerability_id})
    OPTIONAL MATCH (f:SecurityFinding)-[:IDENTIFIES_VULNERABILITY]->(v)
    OPTIONAL MATCH (repo:Repository)-[:HAS_SECURITY_FINDING]->(f)
    OPTIONAL MATCH (f)-[:AFFECTS_DEPENDENCY]->(dep:Dependency)
    OPTIONAL MATCH (repo)-[:HAS_ARTIFACT]->(art:Artifact)
    OPTIONAL MATCH (art)-[:HAS_DEPLOYMENT]->(d:Deployment)
    OPTIONAL MATCH (d)-[:DEPLOYS]->(svc:Service)
    OPTIONAL MATCH (d)-[:DEPLOYED_TO]->(env:Environment)
    RETURN
        {
            id: v.id,
            identifier: v.identifier,
            severity: v.severity,
            summary: v.summary
        } AS vulnerability,
        collect(DISTINCT CASE WHEN f IS NOT NULL THEN {
            id: f.id,
            title: f.title,
            severity: f.severity,
            status: f.status
        } ELSE null END) AS findings,
        collect(DISTINCT CASE WHEN dep IS NOT NULL THEN {
            id: dep.id,
            name: dep.name,
            version: dep.version
        } ELSE null END) AS affected_dependencies,
        collect(DISTINCT CASE WHEN repo IS NOT NULL THEN {
            id: repo.id,
            name: repo.name
        } ELSE null END) AS repositories,
        collect(DISTINCT CASE WHEN svc IS NOT NULL THEN {
            id: svc.id,
            name: svc.name
        } ELSE null END) AS services,
        collect(DISTINCT CASE WHEN env IS NOT NULL THEN {
            id: env.id,
            name: env.name,
            environment_type: env.environment_type
        } ELSE null END) AS environments
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(query, vulnerability_id=vulnerability_id)
            record = result.single()
            if not record or not record["vulnerability"] or not record["vulnerability"]["id"]:
                return None

            clean_findings = [f for f in record["findings"] if f]
            clean_deps = [d for d in record["affected_dependencies"] if d]
            clean_repos = [r for r in record["repositories"] if r]
            clean_svcs = [s for s in record["services"] if s]
            clean_envs = [e for e in record["environments"] if e]

            return {
                "vulnerability": record["vulnerability"],
                "findings": clean_findings,
                "affected_dependencies": clean_deps,
                "repositories": clean_repos,
                "services": clean_svcs,
                "environments": clean_envs,
            }
    finally:
        driver.close()


def get_developer_impact(developer_id: str) -> dict[str, Any] | None:
    query = """
    MATCH (dev:Developer {id: $developer_id})
    OPTIONAL MATCH (c:Commit)-[:AUTHORED_BY]->(dev)
    OPTIONAL MATCH (repo:Repository)-[:HAS_COMMIT]->(c)
    OPTIONAL MATCH (b:Build)-[:BUILDS_FROM]->(c)
    OPTIONAL MATCH (b)-[:PRODUCES]->(art:Artifact)
    OPTIONAL MATCH (art)-[:HAS_DEPLOYMENT]->(d:Deployment)
    OPTIONAL MATCH (d)-[:DEPLOYS]->(svc:Service)
    OPTIONAL MATCH (d)-[:DEPLOYED_TO]->(env:Environment)
    RETURN
        {
            id: dev.id,
            username: dev.username,
            display_name: dev.display_name,
            email: dev.email
        } AS developer,
        collect(DISTINCT CASE WHEN c IS NOT NULL THEN {
            id: c.id,
            sha: c.sha,
            message: c.message
        } ELSE null END) AS commits,
        collect(DISTINCT CASE WHEN repo IS NOT NULL THEN {
            id: repo.id,
            name: repo.name
        } ELSE null END) AS repositories,
        collect(DISTINCT CASE WHEN svc IS NOT NULL THEN {
            id: svc.id,
            name: svc.name
        } ELSE null END) AS deployed_services,
        collect(DISTINCT CASE WHEN env IS NOT NULL THEN {
            id: env.id,
            name: env.name,
            environment_type: env.environment_type
        } ELSE null END) AS environments
    """
    driver = get_driver()
    try:
        with driver.session() as session:
            result = session.run(query, developer_id=developer_id)
            record = result.single()
            if not record or not record["developer"] or not record["developer"]["id"]:
                return None

            clean_commits = [c for c in record["commits"] if c]
            clean_repos = [r for r in record["repositories"] if r]
            clean_svcs = [s for s in record["deployed_services"] if s]
            clean_envs = [e for e in record["environments"] if e]

            return {
                "developer": record["developer"],
                "commits": clean_commits,
                "repositories": clean_repos,
                "deployed_services": clean_svcs,
                "environments": clean_envs,
            }
    finally:
        driver.close()
