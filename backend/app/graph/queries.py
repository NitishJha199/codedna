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
