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
def security_fixture():
    run_id = str(uuid.uuid4())[:8]
    org_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    repo_id = str(uuid.uuid4())
    dep_id = str(uuid.uuid4())
    vuln_id = str(uuid.uuid4())
    finding_id = str(uuid.uuid4())
    pipeline_id = str(uuid.uuid4())
    build_id = str(uuid.uuid4())
    artifact_id = str(uuid.uuid4())
    service_id = str(uuid.uuid4())
    env_id = str(uuid.uuid4())
    deployment_id = str(uuid.uuid4())

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # 1. Organization, Project, Repository
            cur.execute(
                """
                INSERT INTO organizations (id, name, provider, external_id)
                VALUES (%s, 'Sec Org', 'github', %s)
                """,
                (org_id, f"sec-org-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO projects (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'Sec Project', 'github', %s)
                """,
                (project_id, org_id, f"sec-proj-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO repositories (id, project_id, name, provider, external_id)
                VALUES (%s, %s, 'sec-repo', 'github', %s)
                """,
                (repo_id, project_id, f"sec-repo-{run_id}"),
            )

            # 2. Dependency, Vulnerability, Finding
            cur.execute(
                """
                INSERT INTO dependencies (id, repository_id, name, version, package_manager, provider, external_id)
                VALUES (%s, %s, 'requests', '2.25.0', 'pip', 'github', %s)
                """,
                (dep_id, repo_id, f"dep-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO vulnerabilities (id, provider, external_id, identifier, severity, summary)
                VALUES (%s, 'github', %s, %s, 'HIGH', 'Remote code execution in requests')
                """,
                (vuln_id, f"vuln-ext-{run_id}", f"CVE-2026-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO security_findings (
                    id, repository_id, dependency_id, vulnerability_id,
                    provider, external_id, finding_type, severity, status, title
                )
                VALUES (%s, %s, %s, %s, 'github', %s, 'vulnerability', 'HIGH', 'open', 'Critical dependency issue')
                """,
                (finding_id, repo_id, dep_id, vuln_id, f"finding-{run_id}"),
            )

            # 3. Delivery & Runtime (Pipeline -> Build -> Artifact -> Deployment -> Service / Env)
            cur.execute(
                """
                INSERT INTO pipelines (id, repository_id, name, provider, external_id)
                VALUES (%s, %s, 'sec-pipe', 'github_actions', %s)
                """,
                (pipeline_id, repo_id, f"pipe-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO builds (id, pipeline_id, provider, external_id, status)
                VALUES (%s, %s, 'github_actions', %s, 'success')
                """,
                (build_id, pipeline_id, f"build-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO artifacts (id, repository_id, build_id, name, version, artifact_type, provider, external_id)
                VALUES (%s, %s, %s, 'sec-service', 'v2.0.0', 'docker_image', 'github', %s)
                """,
                (artifact_id, repo_id, build_id, f"art-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO services (id, organization_id, name, provider, external_id)
                VALUES (%s, %s, 'sec-payment-api', 'github', %s)
                """,
                (service_id, org_id, f"svc-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO environments (id, organization_id, name, environment_type, provider, external_id)
                VALUES (%s, %s, 'Production EU', 'production', 'github', %s)
                """,
                (env_id, org_id, f"env-{run_id}"),
            )

            cur.execute(
                """
                INSERT INTO deployments (
                    id, environment_id, service_id, artifact_id,
                    provider, external_id, status, deployed_at
                )
                VALUES (%s, %s, %s, %s, 'github', %s, 'success', NOW())
                """,
                (deployment_id, env_id, service_id, artifact_id, f"dep-{run_id}"),
            )
        conn.commit()

        neo4j_driver = get_driver()
        try:
            project_security_graph(conn, neo4j_driver)
        finally:
            neo4j_driver.close()

    yield {
        "vulnerability_id": vuln_id,
        "identifier": f"CVE-2026-{run_id}",
        "repository_name": 'sec-repo',
        "service_name": 'sec-payment-api',
        "environment_name": 'Production EU',
    }


def test_get_vulnerability_impact_success(security_fixture):
    vuln_id = security_fixture["vulnerability_id"]
    response = client.get(f"/lineage/vulnerabilities/{vuln_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["vulnerability"]["id"] == vuln_id
    assert data["vulnerability"]["identifier"] == security_fixture["identifier"]
    assert any(repo["name"] == security_fixture["repository_name"] for repo in data["repositories"])
    assert any(svc["name"] == security_fixture["service_name"] for svc in data["services"])
    assert any(env["name"] == security_fixture["environment_name"] for env in data["environments"])


def test_get_vulnerability_impact_not_found():
    response = client.get("/lineage/vulnerabilities/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
