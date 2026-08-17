from neo4j import Driver
from psycopg import Connection


ORGANIZATION_QUERY = """
    SELECT id, name, provider, external_id
    FROM organizations
"""

PROJECT_QUERY = """
    SELECT id, organization_id, name, provider, external_id
    FROM projects
"""

REPOSITORY_QUERY = """
    SELECT id, project_id, name, provider, external_id, url
    FROM repositories
"""


def project_organizations(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(ORGANIZATION_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Organization {id: $id})
                SET n.name = $name,
                    n.provider = $provider,
                    n.external_id = $external_id
                """,
                id=str(row[0]),
                name=row[1],
                provider=row[2],
                external_id=row[3],
            ).consume()

    return len(rows)


def project_projects(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(PROJECT_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Project {id: $id})
                SET n.name = $name,
                    n.provider = $provider,
                    n.external_id = $external_id

                WITH n
                MATCH (o:Organization {id: $organization_id})
                MERGE (o)-[:CONTAINS]->(n)
                """,
                id=str(row[0]),
                organization_id=str(row[1]),
                name=row[2],
                provider=row[3],
                external_id=row[4],
            ).consume()

    return len(rows)


def project_repositories(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(REPOSITORY_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Repository {id: $id})
                SET n.name = $name,
                    n.provider = $provider,
                    n.external_id = $external_id,
                    n.url = $url

                WITH n
                MATCH (p:Project {id: $project_id})
                MERGE (p)-[:CONTAINS]->(n)
                """,
                id=str(row[0]),
                project_id=str(row[1]),
                name=row[2],
                provider=row[3],
                external_id=row[4],
                url=row[5],
            ).consume()

    return len(rows)


def project_core_graph(
    postgres: Connection,
    neo4j: Driver,
) -> dict[str, int]:
    organizations = project_organizations(postgres, neo4j)
    projects = project_projects(postgres, neo4j)
    repositories = project_repositories(postgres, neo4j)

    return {
        "organizations": organizations,
        "projects": projects,
        "repositories": repositories,
    }


COMMIT_QUERY = """
    SELECT
        id,
        repository_id,
        developer_id,
        provider,
        external_id,
        sha,
        message,
        occurred_at
    FROM commits
"""

PULL_REQUEST_QUERY = """
    SELECT
        id,
        repository_id,
        author_id,
        provider,
        external_id,
        number,
        title,
        state,
        source_branch,
        target_branch,
        created_at
    FROM pull_requests
"""


def project_commits(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(COMMIT_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Commit {id: $id})
                SET n.provider = $provider,
                    n.external_id = $external_id,
                    n.sha = $sha,
                    n.message = $message,
                    n.occurred_at = $occurred_at

                WITH n
                MATCH (r:Repository {id: $repository_id})
                MERGE (r)-[:HAS_COMMIT]->(n)

                WITH n
                OPTIONAL MATCH (d:Developer {id: $developer_id})
                FOREACH (_ IN CASE
                    WHEN d IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (n)-[:AUTHORED_BY]->(d)
                )
                """,
                id=str(row[0]),
                repository_id=str(row[1]),
                developer_id=str(row[2]) if row[2] else None,
                provider=row[3],
                external_id=row[4],
                sha=row[5],
                message=row[6],
                occurred_at=row[7],
            ).consume()

    return len(rows)


def project_pull_requests(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(PULL_REQUEST_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:PullRequest {id: $id})
                SET n.provider = $provider,
                    n.external_id = $external_id,
                    n.number = $number,
                    n.title = $title,
                    n.state = $state,
                    n.source_branch = $source_branch,
                    n.target_branch = $target_branch,
                    n.created_at = $created_at

                WITH n
                MATCH (r:Repository {id: $repository_id})
                MERGE (r)-[:HAS_PULL_REQUEST]->(n)

                WITH n
                OPTIONAL MATCH (d:Developer {id: $author_id})
                FOREACH (_ IN CASE
                    WHEN d IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (n)-[:AUTHORED_BY]->(d)
                )
                """,
                id=str(row[0]),
                repository_id=str(row[1]),
                author_id=str(row[2]) if row[2] else None,
                provider=row[3],
                external_id=row[4],
                number=row[5],
                title=row[6],
                state=row[7],
                source_branch=row[8],
                target_branch=row[9],
                created_at=row[10],
            ).consume()

    return len(rows)


def project_source_graph(
    postgres: Connection,
    neo4j: Driver,
) -> dict[str, int]:
    result = project_core_graph(postgres, neo4j)

    result["commits"] = project_commits(postgres, neo4j)
    result["pull_requests"] = project_pull_requests(postgres, neo4j)

    return result


PIPELINE_QUERY = """
    SELECT
        id,
        repository_id,
        provider,
        external_id,
        name,
        status,
        branch,
        commit_id,
        started_at,
        finished_at
    FROM pipelines
"""

BUILD_QUERY = """
    SELECT
        id,
        pipeline_id,
        commit_id,
        provider,
        external_id,
        status,
        started_at,
        finished_at
    FROM builds
"""

ARTIFACT_QUERY = """
    SELECT
        id,
        build_id,
        repository_id,
        provider,
        external_id,
        name,
        version,
        artifact_type,
        digest
    FROM artifacts
"""

CONTAINER_IMAGE_QUERY = """
    SELECT
        id,
        artifact_id,
        repository_id,
        registry,
        image_name,
        tag,
        digest
    FROM container_images
"""

SBOM_QUERY = """
    SELECT
        id,
        artifact_id,
        container_image_id,
        format,
        version,
        digest,
        generated_at,
        payload
    FROM sboms
"""


def project_pipelines(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(PIPELINE_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Pipeline {id: $id})
                SET n.provider = $provider,
                    n.external_id = $external_id,
                    n.name = $name,
                    n.status = $status,
                    n.branch = $branch,
                    n.started_at = $started_at,
                    n.finished_at = $finished_at

                WITH n
                MATCH (r:Repository {id: $repository_id})
                MERGE (r)-[:HAS_PIPELINE]->(n)

                WITH n
                OPTIONAL MATCH (c:Commit {id: $commit_id})
                FOREACH (_ IN CASE
                    WHEN c IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (n)-[:BUILDS_FROM]->(c)
                )
                """,
                id=str(row[0]),
                repository_id=str(row[1]),
                provider=row[2],
                external_id=row[3],
                name=row[4],
                status=row[5],
                branch=row[6],
                commit_id=str(row[7]) if row[7] else None,
                started_at=row[8],
                finished_at=row[9],
            ).consume()

    return len(rows)


def project_builds(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(BUILD_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Build {id: $id})
                SET n.provider = $provider,
                    n.external_id = $external_id,
                    n.status = $status,
                    n.started_at = $started_at,
                    n.finished_at = $finished_at

                WITH n
                MATCH (p:Pipeline {id: $pipeline_id})
                MERGE (p)-[:HAS_BUILD]->(n)

                WITH n
                OPTIONAL MATCH (c:Commit {id: $commit_id})
                FOREACH (_ IN CASE
                    WHEN c IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (n)-[:BUILDS_FROM]->(c)
                )
                """,
                id=str(row[0]),
                pipeline_id=str(row[1]),
                commit_id=str(row[2]) if row[2] else None,
                provider=row[3],
                external_id=row[4],
                status=row[5],
                started_at=row[6],
                finished_at=row[7],
            ).consume()

    return len(rows)


def project_artifacts(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(ARTIFACT_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Artifact {id: $id})
                SET n.provider = $provider,
                    n.external_id = $external_id,
                    n.name = $name,
                    n.version = $version,
                    n.artifact_type = $artifact_type,
                    n.digest = $digest

                WITH n
                OPTIONAL MATCH (b:Build {id: $build_id})
                FOREACH (_ IN CASE
                    WHEN b IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (b)-[:PRODUCES]->(n)
                )

                WITH n
                OPTIONAL MATCH (r:Repository {id: $repository_id})
                FOREACH (_ IN CASE
                    WHEN r IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (r)-[:HAS_ARTIFACT]->(n)
                )
                """,
                id=str(row[0]),
                build_id=str(row[1]) if row[1] else None,
                repository_id=str(row[2]) if row[2] else None,
                provider=row[3],
                external_id=row[4],
                name=row[5],
                version=row[6],
                artifact_type=row[7],
                digest=row[8],
            ).consume()

    return len(rows)


def project_container_images(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(CONTAINER_IMAGE_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:ContainerImage {id: $id})
                SET n.registry = $registry,
                    n.image_name = $image_name,
                    n.tag = $tag,
                    n.digest = $digest

                WITH n
                OPTIONAL MATCH (a:Artifact {id: $artifact_id})
                FOREACH (_ IN CASE
                    WHEN a IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (a)-[:HAS_CONTAINER_IMAGE]->(n)
                )

                WITH n
                OPTIONAL MATCH (r:Repository {id: $repository_id})
                FOREACH (_ IN CASE
                    WHEN r IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (r)-[:HAS_CONTAINER_IMAGE]->(n)
                )
                """,
                id=str(row[0]),
                artifact_id=str(row[1]) if row[1] else None,
                repository_id=str(row[2]) if row[2] else None,
                registry=row[3],
                image_name=row[4],
                tag=row[5],
                digest=row[6],
            ).consume()

    return len(rows)


def project_sboms(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(SBOM_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:SBOM {id: $id})
                SET n.format = $format,
                    n.version = $version,
                    n.digest = $digest,
                    n.generated_at = $generated_at

                WITH n
                OPTIONAL MATCH (a:Artifact {id: $artifact_id})
                FOREACH (_ IN CASE
                    WHEN a IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (a)-[:HAS_SBOM]->(n)
                )

                WITH n
                OPTIONAL MATCH (i:ContainerImage {id: $container_image_id})
                FOREACH (_ IN CASE
                    WHEN i IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (i)-[:HAS_SBOM]->(n)
                )
                """,
                id=str(row[0]),
                artifact_id=str(row[1]) if row[1] else None,
                container_image_id=str(row[2]) if row[2] else None,
                format=row[3],
                version=row[4],
                digest=row[5],
                generated_at=row[6],
            ).consume()

    return len(rows)


def project_delivery_graph(
    postgres: Connection,
    neo4j: Driver,
) -> dict[str, int]:
    result = project_source_graph(postgres, neo4j)

    result["pipelines"] = project_pipelines(postgres, neo4j)
    result["builds"] = project_builds(postgres, neo4j)
    result["artifacts"] = project_artifacts(postgres, neo4j)
    result["container_images"] = project_container_images(postgres, neo4j)
    result["sboms"] = project_sboms(postgres, neo4j)

    return result


ENVIRONMENT_QUERY = """
    SELECT
        id,
        organization_id,
        name,
        environment_type,
        provider,
        external_id
    FROM environments
"""

SERVICE_QUERY = """
    SELECT
        id,
        organization_id,
        name,
        provider,
        external_id
    FROM services
"""

DEPLOYMENT_QUERY = """
    SELECT
        id,
        environment_id,
        service_id,
        artifact_id,
        container_image_id,
        provider,
        external_id,
        status,
        deployed_at
    FROM deployments
"""


def project_environments(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(ENVIRONMENT_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Environment {id: $id})
                SET n.name = $name,
                    n.environment_type = $environment_type,
                    n.provider = $provider,
                    n.external_id = $external_id

                WITH n
                OPTIONAL MATCH (o:Organization {id: $organization_id})
                FOREACH (_ IN CASE
                    WHEN o IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (o)-[:CONTAINS]->(n)
                )
                """,
                id=str(row[0]),
                organization_id=str(row[1]) if row[1] else None,
                name=row[2],
                environment_type=row[3],
                provider=row[4],
                external_id=row[5],
            ).consume()

    return len(rows)


def project_services(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(SERVICE_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Service {id: $id})
                SET n.name = $name,
                    n.provider = $provider,
                    n.external_id = $external_id

                WITH n
                OPTIONAL MATCH (o:Organization {id: $organization_id})
                FOREACH (_ IN CASE
                    WHEN o IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (o)-[:OWNS]->(n)
                )
                """,
                id=str(row[0]),
                organization_id=str(row[1]) if row[1] else None,
                name=row[2],
                provider=row[3],
                external_id=row[4],
            ).consume()

    return len(rows)


def project_deployments(
    postgres: Connection,
    neo4j: Driver,
) -> int:
    with postgres.cursor() as cursor:
        cursor.execute(DEPLOYMENT_QUERY)
        rows = cursor.fetchall()

    with neo4j.session() as session:
        for row in rows:
            session.run(
                """
                MERGE (n:Deployment {id: $id})
                SET n.provider = $provider,
                    n.external_id = $external_id,
                    n.status = $status,
                    n.deployed_at = $deployed_at

                WITH n
                OPTIONAL MATCH (e:Environment {id: $environment_id})
                FOREACH (_ IN CASE
                    WHEN e IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (n)-[:DEPLOYED_TO]->(e)
                )

                WITH n
                OPTIONAL MATCH (s:Service {id: $service_id})
                FOREACH (_ IN CASE
                    WHEN s IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (n)-[:DEPLOYS]->(s)
                )

                WITH n
                OPTIONAL MATCH (a:Artifact {id: $artifact_id})
                FOREACH (_ IN CASE
                    WHEN a IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (a)-[:HAS_DEPLOYMENT]->(n)
                )

                WITH n
                OPTIONAL MATCH (i:ContainerImage {id: $container_image_id})
                FOREACH (_ IN CASE
                    WHEN i IS NULL THEN []
                    ELSE [1]
                END |
                    MERGE (i)-[:HAS_DEPLOYMENT]->(n)
                )
                """,
                id=str(row[0]),
                environment_id=str(row[1]) if row[1] else None,
                service_id=str(row[2]) if row[2] else None,
                artifact_id=str(row[3]) if row[3] else None,
                container_image_id=str(row[4]) if row[4] else None,
                provider=row[5],
                external_id=row[6],
                status=row[7],
                deployed_at=row[8],
            ).consume()

    return len(rows)


def project_runtime_graph(
    postgres: Connection,
    neo4j: Driver,
) -> dict[str, int]:
    result = project_delivery_graph(postgres, neo4j)

    result["environments"] = project_environments(postgres, neo4j)
    result["services"] = project_services(postgres, neo4j)
    result["deployments"] = project_deployments(postgres, neo4j)

    return result
