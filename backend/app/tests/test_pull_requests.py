import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_pull_request():
    repository_id = str(uuid.uuid4())

    payload = {
        "repository_id": repository_id,
        "provider": "pytest",
        "external_id": f"pr-{uuid.uuid4()}",
        "number": 1,
        "title": "Add CodeDNA integration",
        "state": "open",
        "source_branch": "feature/codedna",
        "target_branch": "main",
    }

    response = client.post("/pull-requests", json=payload)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Repository or author does not exist."
    }


def test_pull_request_requires_existing_repository():
    payload = {
        "repository_id": "00000000-0000-0000-0000-000000000000",
        "provider": "pytest",
        "external_id": f"pr-{uuid.uuid4()}",
        "number": 2,
        "title": "Orphan pull request",
    }

    response = client.post("/pull-requests", json=payload)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Repository or author does not exist."
    }


def test_pull_request_invalid_payload():
    response = client.post(
        "/pull-requests",
        json={
            "repository_id": "not-a-uuid",
            "provider": "pytest",
            "external_id": "invalid-001",
        },
    )

    assert response.status_code == 422
