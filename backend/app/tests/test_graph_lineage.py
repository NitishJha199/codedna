import uuid
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from backend.app.main import app
from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import (
    project_core_graph,
    project_source_graph,
    project_delivery_graph,
    project_runtime_graph,
)

client = TestClient(app)


@pytest.fixture
def lineage_fixture():
    run_id = str(uuid.uuid4())[:8]
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    repo_id = str(uuid.uuid4())
    dev_id = str(uuid.uuid4())
    commit_id = str(uuid.uuid4())
    pipeline_id = str(uuid.uuid4())
    build_id = str(uuid.uuid4())
    artifact_id = str(uuid.uuid4())
    service_id = str(uuid.uuid4())
    env_id = str(uuid.uuid4())
    deployment_id = str(uuid.uuid4())

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # 1. Organization & Project
            cur.execute(
                """
                INSERT INTO organizations (id, name, provider, external_id)
                VALUES (%s, 'Lineage Org', 'github', %s)
                """,
                (org_id, f"lineage-org-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO projects (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'Lineage Project', 'github', %s)
                """,
                (project_id, org_id, f"lineage-proj-{run_id}"),
            )

            # 2. Repository & Developer
            cur.execute(
                """
                INSERT INTO repositories (id, project_id, name, provider, external_id)
                VALUES (%s, %s, 'lineage-repo', 'github', %s)
                """,
                (repo_id, project_id, f"lin-repo-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO developers (id, organization_id, username, display_name, email, provider, external_id)
                VALUES (%s, %s, 'lineagedev', 'Lineage Dev', 'dev@lineage.codedna', 'github', %s)
                """,
                (dev_id, org_id, f"dev-lin-{run_id}"),
            )

            # 3. Commit
            cur.execute(
                """
                INSERT INTO commits (id, repository_id, developer_id, provider, external_id, sha, message)
                VALUES (%s, %s, %s, 'github', %s, %s, 'feat: initial lineage build')
                """,
                (commit_id, repo_id, dev_id, f"c-lin-{run_id}", f"sha-{run_id}"),
            )

            # 4. Pipeline & Build
            cur.execute(
                """
                INSERT INTO pipelines (id, repository_id, name, provider, external_id)
                VALUES (%s, %s, 'lineage-ci', 'github_actions', %s)
                """,
                (pipeline_id, repo_id, f"pipe-lin-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO builds (id, pipeline_id, commit_id, provider, external_id, status)
                VALUES (%s, %s, %s, 'github_actions', %s, 'success')
                """,
                (build_id, pipeline_id, commit_id, f"build-lin-{run_id}"),
            )

            # 5. Artifact
            cur.execute(
                """
                INSERT INTO artifacts (id, repository_id, build_id, name, version, artifact_type, provider, external_id)
                VALUES (%s, %s, %s, 'lineage-api-service', 'v1.0.0', 'docker_image', 'github', %s)
                """,
                (artifact_id, repo_id, build_id, f"art-lin-{run_id}"),
            )

            # 6. Service & Environment
            cur.execute(
                """
                INSERT INTO services (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'lineage-api', 'github', %s)
                """,
                (service_id, org_id, f"lineage-svc-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO environments (id, organization_id, name, environment_type, provider, external_id)
                VALUES (%s, %s, 'Lineage Prod', 'production', 'github', %s)
                """,
                (env_id, org_id, f"lineage-env-{run_id}"),
            )

            # 7. Deployment
            cur.execute(
                """
                INSERT INTO deployments (
                    id, environment_id, service_id, artifact_id,
                    provider, external_id, status, deployed_at
                )
                VALUES (%s, %s, %s, %s, 'github', %s, 'success', NOW())
                """,
                (deployment_id, env_id, service_id, artifact_id, f"dep-lin-{run_id}"),
            )
        conn.commit()

        neo4j_driver = get_driver()
        try:
            project_core_graph(conn, neo4j_driver)
            project_source_graph(conn, neo4j_driver)
            project_delivery_graph(conn, neo4j_driver)
            project_runtime_graph(conn, neo4j_driver)
        finally:
            neo4j_driver.close()

    yield {
        "deployment_id": deployment_id,
        "artifact_id": artifact_id,
        "service_id": service_id,
        "environment_id": env_id,
        "build_id": build_id,
        "pipeline_id": pipeline_id,
        "repository_id": repo_id,
        "commit_id": commit_id,
        "commit_sha": f"sha-{run_id}",
    }


def test_get_deployment_lineage_success(lineage_fixture):
    deployment_id = lineage_fixture["deployment_id"]
    response = client.get(f"/lineage/deployments/{deployment_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["deployment"]["id"] == deployment_id
    assert data["deployment"]["status"] == "success"
    assert data["environment"]["name"] == "Lineage Prod"
    assert data["service"]["name"] == "lineage-api"
    assert data["artifact"]["name"] == "lineage-api-service"
    assert data["build"]["status"] == "success"
    assert data["pipeline"]["name"] == "lineage-ci"
    assert data["repository"]["name"] == "lineage-repo"
    assert data["commit"]["sha"] == lineage_fixture["commit_sha"]


def test_get_deployment_lineage_not_found():
    response = client.get("/lineage/deployments/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
