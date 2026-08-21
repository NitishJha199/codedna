import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from backend.app.main import app
from backend.app.db.postgres import get_connection

client = TestClient(app)


@pytest.fixture
def dora_fixture():
    run_id = str(uuid.uuid4())[:8]
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    repo_id = str(uuid.uuid4())
    service_id = str(uuid.uuid4())
    env_id = str(uuid.uuid4())
    dev_id = str(uuid.uuid4())
    commit_id = str(uuid.uuid4())
    pipeline_id = str(uuid.uuid4())
    build_id = str(uuid.uuid4())
    artifact_id = str(uuid.uuid4())
    dep_success_id = str(uuid.uuid4())
    dep_failed_id = str(uuid.uuid4())

    now = datetime.now(timezone.utc)
    commit_time = now - timedelta(hours=2)
    deploy_time = now - timedelta(hours=1)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Org, Project, Repo, Developer, Service, Env
            cur.execute(
                """
                INSERT INTO organizations (id, name, provider, external_id)
                VALUES (%s, 'DORA Org', 'github', %s)
                """,
                (org_id, f"dora-org-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO projects (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'DORA Project', 'github', %s)
                """,
                (project_id, org_id, f"dora-proj-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO repositories (id, project_id, name, provider, external_id)
                VALUES (%s, %s, 'dora-repo', 'github', %s)
                """,
                (repo_id, project_id, f"dora-repo-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO developers (id, organization_id, username, display_name, email, provider, external_id)
                VALUES (%s, %s, 'doradev', 'DORA Dev', 'dev@dora.io', 'github', %s)
                """,
                (dev_id, org_id, f"dora-dev-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO services (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'dora-service', 'github', %s)
                """,
                (service_id, org_id, f"dora-svc-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO environments (id, organization_id, name, environment_type, provider, external_id)
                VALUES (%s, %s, 'DORA Prod', 'production', 'github', %s)
                """,
                (env_id, org_id, f"dora-env-{run_id}"),
            )

            # Commit -> Pipeline -> Build -> Artifact
            cur.execute(
                """
                INSERT INTO commits (id, repository_id, developer_id, provider, external_id, sha, message, occurred_at)
                VALUES (%s, %s, %s, 'github', %s, %s, 'dora commit', %s)
                """,
                (commit_id, repo_id, dev_id, f"c-dora-{run_id}", f"sha-dora-{run_id}", commit_time),
            )
            cur.execute(
                """
                INSERT INTO pipelines (id, repository_id, name, provider, external_id)
                VALUES (%s, %s, 'dora-pipe', 'github_actions', %s)
                """,
                (pipeline_id, repo_id, f"pipe-dora-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO builds (id, pipeline_id, commit_id, provider, external_id, status)
                VALUES (%s, %s, %s, 'github_actions', %s, 'success')
                """,
                (build_id, pipeline_id, commit_id, f"build-dora-{run_id}"),
            )
            cur.execute(
                """
                INSERT INTO artifacts (id, repository_id, build_id, name, version, artifact_type, provider, external_id)
                VALUES (%s, %s, %s, 'dora-art', 'v1.0.0', 'docker_image', 'github', %s)
                """,
                (artifact_id, repo_id, build_id, f"art-dora-{run_id}"),
            )

            # 1 Successful Deployment, 1 Failed Deployment
            cur.execute(
                """
                INSERT INTO deployments (
                    id, environment_id, service_id, artifact_id,
                    provider, external_id, status, deployed_at
                )
                VALUES (%s, %s, %s, %s, 'github', %s, 'success', %s)
                """,
                (dep_success_id, env_id, service_id, artifact_id, f"dep-s-{run_id}", deploy_time),
            )
            cur.execute(
                """
                INSERT INTO deployments (
                    id, environment_id, service_id, artifact_id,
                    provider, external_id, status, deployed_at
                )
                VALUES (%s, %s, %s, %s, 'github', %s, 'failed', %s)
                """,
                (dep_failed_id, env_id, service_id, artifact_id, f"dep-f-{run_id}", now),
            )
        conn.commit()

    yield {
        "environment_id": env_id,
        "service_id": service_id,
        "start_time": (now - timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(hours=1)).isoformat(),
    }


def test_dora_metrics_calculation(dora_fixture):
    params = {
        "start_time": dora_fixture["start_time"],
        "end_time": dora_fixture["end_time"],
        "environment_id": dora_fixture["environment_id"],
        "service_id": dora_fixture["service_id"],
    }

    response = client.get("/metrics/dora", params=params)
    assert response.status_code == 200

    data = response.json()
    assert data["deployments"]["total"] == 2
    assert data["deployments"]["successful"] == 1
    assert data["deployments"]["failed"] == 1
    assert data["change_failure_rate"]["rate_percentage"] == 50.0
    assert data["lead_time_for_changes"]["avg_lead_time_seconds"] is not None
    assert data["lead_time_for_changes"]["avg_lead_time_seconds"] > 0
