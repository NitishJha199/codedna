from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_pipeline():
    repository_id = uuid4()

    # Create the required repository chain through the database-backed API.
    organization_response = client.post(
        "/organizations",
        json={
            "name": "Pipeline Test Organization",
            "provider": "pytest",
            "external_id": f"pipeline-org-{uuid4()}",
        },
    )
    assert organization_response.status_code == 201

    project_response = client.post(
        "/projects",
        json={
            "organization_id": organization_response.json()["id"],
            "name": "Pipeline Test Project",
            "provider": "pytest",
            "external_id": f"pipeline-project-{uuid4()}",
        },
    )
    assert project_response.status_code == 201

    repository_response = client.post(
        "/repositories",
        json={
            "project_id": project_response.json()["id"],
            "name": "Pipeline Test Repository",
            "provider": "pytest",
            "external_id": f"pipeline-repository-{uuid4()}",
        },
    )
    assert repository_response.status_code == 201

    response = client.post(
        "/pipelines",
        json={
            "repository_id": repository_response.json()["id"],
            "provider": "pytest",
            "external_id": f"pipeline-{uuid4()}",
            "name": "CI Pipeline",
            "status": "success",
            "branch": "main",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["repository_id"] == repository_response.json()["id"]
    assert body["provider"] == "pytest"
    assert body["name"] == "CI Pipeline"
    assert body["status"] == "success"
    assert body["branch"] == "main"


def test_duplicate_pipeline_returns_conflict():
    repository_id = uuid4()

    organization_response = client.post(
        "/organizations",
        json={
            "name": "Duplicate Pipeline Organization",
            "provider": "pytest",
            "external_id": f"pipeline-duplicate-org-{uuid4()}",
        },
    )
    assert organization_response.status_code == 201

    project_response = client.post(
        "/projects",
        json={
            "organization_id": organization_response.json()["id"],
            "name": "Duplicate Pipeline Project",
            "provider": "pytest",
            "external_id": f"pipeline-duplicate-project-{uuid4()}",
        },
    )
    assert project_response.status_code == 201

    repository_response = client.post(
        "/repositories",
        json={
            "project_id": project_response.json()["id"],
            "name": "Duplicate Pipeline Repository",
            "provider": "pytest",
            "external_id": f"pipeline-duplicate-repository-{uuid4()}",
        },
    )
    assert repository_response.status_code == 201

    payload = {
        "repository_id": repository_response.json()["id"],
        "provider": "pytest",
        "external_id": f"pipeline-duplicate-{uuid4()}",
        "name": "Duplicate Pipeline",
    }

    first_response = client.post("/pipelines", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/pipelines", json=payload)
    assert second_response.status_code == 409


def test_pipeline_with_missing_repository_returns_not_found():
    response = client.post(
        "/pipelines",
        json={
            "repository_id": str(uuid4()),
            "provider": "pytest",
            "external_id": f"pipeline-orphan-{uuid4()}",
            "name": "Orphan Pipeline",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Repository or commit does not exist."
