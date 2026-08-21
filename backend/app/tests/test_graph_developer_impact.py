import uuid
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from backend.app.main import app
from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import project_security_graph

client = TestClient(app)


@pytest.fixture
def developer_fixture():
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
            cur.execute(
                """
                INSERT INTO organizations (id, name, provider, external_id)
                VALUES (%s, 'Dev Impact Org', 'github', %s)
                """,
                (org_id, f"dev-org-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO projects (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'Dev Impact Project', 'github', %s)
                """,
                (project_id, org_id, f"dev-proj-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO repositories (id, project_id, name, provider, external_id)
                VALUES (%s, %s, 'dev-impact-repo', 'github', %s)
                """,
                (repo_id, project_id, f"dev-repo-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO developers (id, organization_id, username, display_name, email, provider, external_id)
                VALUES (%s, %s, 'leaddev', 'Lead Developer', 'lead@codedna.io', 'github', %s)
                """,
                (dev_id, org_id, f"lead-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO commits (id, repository_id, developer_id, provider, external_id, sha, message)
                VALUES (%s, %s, %s, 'github', %s, %s, 'feat: core engine upgrade')
                """,
                (commit_id, repo_id, dev_id, f"c-dev-{run_id}", f"sha-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO pipelines (id, repository_id, name, provider, external_id)
                VALUES (%s, %s, 'dev-pipe', 'github_actions', %s)
                """,
                (pipeline_id, repo_id, f"pipe-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO builds (id, pipeline_id, commit_id, provider, external_id, status)
                VALUES (%s, %s, %s, 'github_actions', %s, 'success')
                """,
                (build_id, pipeline_id, commit_id, f"build-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO artifacts (id, repository_id, build_id, name, version, artifact_type, provider, external_id)
                VALUES (%s, %s, %s, 'engine-svc', 'v3.0.0', 'docker_image', 'github', %s)
                """,
                (artifact_id, repo_id, build_id, f"art-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO services (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'engine-service', 'github', %s)
                """,
                (service_id, org_id, f"svc-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO environments (id, organization_id, name, environment_type, provider, external_id)
                VALUES (%s, %s, 'Production US', 'production', 'github', %s)
                """,
                (env_id, org_id, f"env-dev-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO deployments (
                    id, environment_id, service_id, artifact_id,
                    provider, external_id, status, deployed_at
                )
                VALUES (%s, %s, %s, %s, 'github', %s, 'success', NOW())
                """,
                (deployment_id, env_id, service_id, artifact_id, f"dep-dev-{run_id}"),
            )
        conn.commit()

        neo4j_driver = get_driver()
        try:
            project_security_graph(conn, neo4j_driver)
        finally:
            neo4j_driver.close()

    yield {
        "developer_id": dev_id,
        "username": 'leaddev',
        "commit_sha": f"sha-dev-{run_id}",
        "repository_name": 'dev-impact-repo',
        "service_name": 'engine-service',
        "environment_name": 'Production US',
    }


def test_get_developer_impact_success(developer_fixture):
    dev_id = developer_fixture["developer_id"]
    response = client.get(f"/lineage/developers/{dev_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["developer"]["id"] == dev_id
    assert data["developer"]["username"] == developer_fixture["username"]
    assert any(c["sha"] == developer_fixture["commit_sha"] for c in data["commits"])
    assert any(repo["name"] == developer_fixture["repository_name"] for repo in data["repositories"])
    assert any(svc["name"] == developer_fixture["service_name"] for svc in data["deployed_services"])
    assert any(env["name"] == developer_fixture["environment_name"] for env in data["environments"])


def test_get_developer_impact_not_found():
    response = client.get("/lineage/developers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
