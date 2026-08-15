from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_test_pipeline() -> str:
    organization_response = client.post(
        "/organizations",
        json={
            "name": "Build Test Organization",
            "provider": "pytest",
            "external_id": f"build-org-{uuid4()}",
        },
    )
    assert organization_response.status_code == 201

    project_response = client.post(
        "/projects",
        json={
            "organization_id": organization_response.json()["id"],
            "name": "Build Test Project",
            "provider": "pytest",
            "external_id": f"build-project-{uuid4()}",
        },
    )
    assert project_response.status_code == 201

    repository_response = client.post(
        "/repositories",
        json={
            "project_id": project_response.json()["id"],
            "name": "Build Test Repository",
            "provider": "pytest",
            "external_id": f"build-repository-{uuid4()}",
        },
    )
    assert repository_response.status_code == 201

    pipeline_response = client.post(
        "/pipelines",
        json={
            "repository_id": repository_response.json()["id"],
            "provider": "pytest",
            "external_id": f"build-pipeline-{uuid4()}",
            "name": "Build Test Pipeline",
            "status": "success",
            "branch": "main",
        },
    )
    assert pipeline_response.status_code == 201

    return pipeline_response.json()["id"]


def test_create_build():
    pipeline_id = create_test_pipeline()

    response = client.post(
        "/builds",
        json={
            "pipeline_id": pipeline_id,
            "provider": "pytest",
            "external_id": f"build-{uuid4()}",
            "status": "success",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["pipeline_id"] == pipeline_id
    assert body["provider"] == "pytest"
    assert body["status"] == "success"


def test_duplicate_build_returns_conflict():
    pipeline_id = create_test_pipeline()

    payload = {
        "pipeline_id": pipeline_id,
        "provider": "pytest",
        "external_id": f"duplicate-build-{uuid4()}",
        "status": "success",
    }

    first_response = client.post("/builds", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/builds", json=payload)
    assert second_response.status_code == 409


def test_build_with_missing_pipeline_returns_not_found():
    response = client.post(
        "/builds",
        json={
            "pipeline_id": str(uuid4()),
            "provider": "pytest",
            "external_id": f"orphan-build-{uuid4()}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Pipeline or commit does not exist."
