from neo4j import Driver


GRAPH_CONSTRAINTS = {
    "organization_id": """
        CREATE CONSTRAINT organization_id_unique IF NOT EXISTS
        FOR (n:Organization)
        REQUIRE n.id IS UNIQUE
    """,
    "project_id": """
        CREATE CONSTRAINT project_id_unique IF NOT EXISTS
        FOR (n:Project)
        REQUIRE n.id IS UNIQUE
    """,
    "repository_id": """
        CREATE CONSTRAINT repository_id_unique IF NOT EXISTS
        FOR (n:Repository)
        REQUIRE n.id IS UNIQUE
    """,
    "developer_id": """
        CREATE CONSTRAINT developer_id_unique IF NOT EXISTS
        FOR (n:Developer)
        REQUIRE n.id IS UNIQUE
    """,
    "commit_id": """
        CREATE CONSTRAINT commit_id_unique IF NOT EXISTS
        FOR (n:Commit)
        REQUIRE n.id IS UNIQUE
    """,
    "pull_request_id": """
        CREATE CONSTRAINT pull_request_id_unique IF NOT EXISTS
        FOR (n:PullRequest)
        REQUIRE n.id IS UNIQUE
    """,
    "dependency_id": """
        CREATE CONSTRAINT dependency_id_unique IF NOT EXISTS
        FOR (n:Dependency)
        REQUIRE n.id IS UNIQUE
    """,
    "vulnerability_id": """
        CREATE CONSTRAINT vulnerability_id_unique IF NOT EXISTS
        FOR (n:Vulnerability)
        REQUIRE n.id IS UNIQUE
    """,
    "security_finding_id": """
        CREATE CONSTRAINT security_finding_id_unique IF NOT EXISTS
        FOR (n:SecurityFinding)
        REQUIRE n.id IS UNIQUE
    """,
    "pipeline_id": """
        CREATE CONSTRAINT pipeline_id_unique IF NOT EXISTS
        FOR (n:Pipeline)
        REQUIRE n.id IS UNIQUE
    """,
    "build_id": """
        CREATE CONSTRAINT build_id_unique IF NOT EXISTS
        FOR (n:Build)
        REQUIRE n.id IS UNIQUE
    """,
    "artifact_id": """
        CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS
        FOR (n:Artifact)
        REQUIRE n.id IS UNIQUE
    """,
    "container_image_id": """
        CREATE CONSTRAINT container_image_id_unique IF NOT EXISTS
        FOR (n:ContainerImage)
        REQUIRE n.id IS UNIQUE
    """,
    "sbom_id": """
        CREATE CONSTRAINT sbom_id_unique IF NOT EXISTS
        FOR (n:SBOM)
        REQUIRE n.id IS UNIQUE
    """,
    "environment_id": """
        CREATE CONSTRAINT environment_id_unique IF NOT EXISTS
        FOR (n:Environment)
        REQUIRE n.id IS UNIQUE
    """,
    "service_id": """
        CREATE CONSTRAINT service_id_unique IF NOT EXISTS
        FOR (n:Service)
        REQUIRE n.id IS UNIQUE
    """,
    "deployment_id": """
        CREATE CONSTRAINT deployment_id_unique IF NOT EXISTS
        FOR (n:Deployment)
        REQUIRE n.id IS UNIQUE
    """,
}


def ensure_constraints(driver: Driver) -> None:
    with driver.session() as session:
        for query in GRAPH_CONSTRAINTS.values():
            session.run(query).consume()
