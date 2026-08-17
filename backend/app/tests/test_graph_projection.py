import uuid

from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import (
    project_core_graph,
    project_runtime_graph,
)


def test_project_core_graph():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        result = project_core_graph(postgres, neo4j)

        assert "organizations" in result
        assert "projects" in result
        assert "repositories" in result
        assert result["organizations"] >= 0
        assert result["projects"] >= 0
        assert result["repositories"] >= 0
    finally:
        postgres.close()
        neo4j.close()


def test_core_projection_is_idempotent():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        first = project_core_graph(postgres, neo4j)
        second = project_core_graph(postgres, neo4j)

        assert first == second
    finally:
        postgres.close()
        neo4j.close()


def _create_runtime_fixture():
    organization_id = uuid.uuid4()
    project_id = uuid.uuid4()
    environment_id = uuid.uuid4()
    service_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pipeline_id = uuid.uuid4()
    build_id = uuid.uuid4()
    artifact_id = uuid.uuid4()
    container_image_id = uuid.uuid4()
    deployment_id = uuid.uuid4()

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO organizations
                    (id, name, provider, external_id)
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    organization_id,
                    "Graph Runtime Organization",
                    "pytest",
                    f"graph-org-{organization_id}",
                ),
            )

            cur.execute(
                """
                INSERT INTO environments
                    (id, organization_id, name, environment_type, provider, external_id)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    environment_id,
                    organization_id,
                    "Production",
                    "production",
                    "pytest",
                    f"graph-env-{environment_id}",
                ),
            )

            cur.execute(
                """
                INSERT INTO services
                    (id, organization_id, name, provider, external_id)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                (
                    service_id,
                    organization_id,
                    "CodeDNA API",
                    "pytest",
                    f"graph-service-{service_id}",
                ),
            )

            cur.execute(
                """
                INSERT INTO projects
                    (id, organization_id, name, provider, external_id)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    organization_id,
                    "Graph Runtime Project",
                    "pytest",
                    f"graph-project-{project_id}",
                ),
            )

            cur.execute(
                """
                INSERT INTO repositories
                    (id, project_id, name, provider, external_id, url)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    repository_id,
                    project_id,
                    "Graph Runtime Repository",
                    "pytest",
                    f"graph-repository-{repository_id}",
                    "https://example.com/graph-runtime",
                ),
            )

            cur.execute(
                """
                INSERT INTO pipelines
                    (id, repository_id, provider, external_id, name, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    pipeline_id,
                    repository_id,
                    "pytest",
                    f"graph-pipeline-{pipeline_id}",
                    "runtime-pipeline",
                    "success",
                ),
            )

            cur.execute(
                """
                INSERT INTO builds
                    (id, pipeline_id, provider, external_id, status)
                VALUES
                    (%s, %s, %s, %s, %s)
                """,
                (
                    build_id,
                    pipeline_id,
                    "pytest",
                    f"graph-build-{build_id}",
                    "success",
                ),
            )

            cur.execute(
                """
                INSERT INTO artifacts
                    (id, build_id, repository_id, provider, external_id,
                     name, version, artifact_type, digest)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    artifact_id,
                    build_id,
                    repository_id,
                    "pytest",
                    f"graph-artifact-{artifact_id}",
                    "codedna-api",
                    "1.0.0",
                    "container",
                    "sha256:graph-runtime-artifact",
                ),
            )

            cur.execute(
                """
                INSERT INTO container_images
                    (id, artifact_id, repository_id, registry, image_name, tag, digest)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    container_image_id,
                    artifact_id,
                    repository_id,
                    "pytest-registry",
                    "codedna-api",
                    "1.0.0",
                    "sha256:graph-runtime-image",
                ),
            )

            cur.execute(
                """
                INSERT INTO deployments
                    (id, environment_id, service_id, artifact_id,
                     container_image_id, provider, external_id, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    deployment_id,
                    environment_id,
                    service_id,
                    artifact_id,
                    container_image_id,
                    "pytest",
                    f"graph-deployment-{deployment_id}",
                    "success",
                ),
            )

        conn.commit()

    finally:
        conn.close()

    return {
        "organization_id": organization_id,
        "environment_id": environment_id,
        "service_id": service_id,
        "repository_id": repository_id,
        "pipeline_id": pipeline_id,
        "build_id": build_id,
        "artifact_id": artifact_id,
        "container_image_id": container_image_id,
        "deployment_id": deployment_id,
    }


def test_runtime_projection_creates_runtime_graph():
    fixture = _create_runtime_fixture()

    postgres = get_connection()
    neo4j = get_driver()

    try:
        result = project_runtime_graph(postgres, neo4j)

        assert result["environments"] >= 1
        assert result["services"] >= 1
        assert result["deployments"] >= 1

        with neo4j.session() as session:
            record = session.run(
                """
                MATCH (o:Organization {id: $organization_id})
                      -[:CONTAINS]->
                      (e:Environment {id: $environment_id})

                MATCH (o)-[:OWNS]->(s:Service {id: $service_id})

                MATCH (r:Repository {id: $repository_id})
                      -[:HAS_PIPELINE]->
                      (p:Pipeline {id: $pipeline_id})
                      -[:HAS_BUILD]->
                      (b:Build {id: $build_id})
                      -[:PRODUCES]->
                      (a:Artifact {id: $artifact_id})

                MATCH (a)-[:HAS_CONTAINER_IMAGE]->
                      (i:ContainerImage {id: $container_image_id})

                MATCH (a)-[:HAS_DEPLOYMENT]->
                      (d:Deployment {id: $deployment_id})
                      -[:DEPLOYED_TO]->
                      (e)

                MATCH (d)-[:DEPLOYS]->(s)

                RETURN count(*) AS count
                """,
                **{key: str(value) for key, value in fixture.items()},
            ).single()

            assert record["count"] == 1

    finally:
        postgres.close()
        neo4j.close()


def test_runtime_projection_is_idempotent():
    fixture = _create_runtime_fixture()

    postgres = get_connection()
    neo4j = get_driver()

    try:
        first = project_runtime_graph(postgres, neo4j)
        second = project_runtime_graph(postgres, neo4j)

        assert first == second

        with neo4j.session() as session:
            counts = session.run(
                """
                MATCH (d:Deployment {id: $deployment_id})
                OPTIONAL MATCH (d)-[:DEPLOYED_TO]->(e:Environment)
                OPTIONAL MATCH (d)-[:DEPLOYS]->(s:Service)
                OPTIONAL MATCH (a:Artifact {id: $artifact_id})
                      -[:HAS_DEPLOYMENT]->(d)
                RETURN
                    count(DISTINCT d) AS deployments,
                    count(DISTINCT e) AS environments,
                    count(DISTINCT s) AS services,
                    count(DISTINCT a) AS artifacts
                """,
                deployment_id=str(fixture["deployment_id"]),
                artifact_id=str(fixture["artifact_id"]),
            ).single()

            assert counts["deployments"] == 1
            assert counts["environments"] == 1
            assert counts["services"] == 1
            assert counts["artifacts"] == 1

    finally:
        postgres.close()
        neo4j.close()
