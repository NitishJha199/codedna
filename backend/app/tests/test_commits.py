from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_commit():
    response = client.post(
        "/commits",
        json={
            "repository_id": "1dc68fa2-906a-4376-944d-59b128b72132",
            "provider": "pytest",
            "external_id": f"pytest-commit-{uuid4()}",
            "sha": f"pytest-sha-{uuid4()}",
            "message": "Pytest commit",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["repository_id"] == "1dc68fa2-906a-4376-944d-59b128b72132"
    assert data["provider"] == "pytest"
    assert data["message"] == "Pytest commit"
    assert data["developer_id"] is None


def test_duplicate_commit_returns_conflict():
    external_id = f"pytest-duplicate-{uuid4()}"
    sha = f"pytest-duplicate-sha-{uuid4()}"

    payload = {
        "repository_id": "1dc68fa2-906a-4376-944d-59b128b72132",
        "provider": "pytest",
        "external_id": external_id,
        "sha": sha,
        "message": "Duplicate test",
    }

    first_response = client.post("/commits", json=payload)

    assert first_response.status_code == 201

    second_response = client.post(
        "/commits",
        json={
            **payload,
            "message": "Duplicate attempt",
        },
    )

    assert second_response.status_code == 409


def test_commit_with_nonexistent_repository_returns_not_found():
    response = client.post(
        "/commits",
        json={
            "repository_id": "00000000-0000-0000-0000-000000000000",
            "provider": "pytest",
            "external_id": f"pytest-orphan-{uuid4()}",
            "sha": f"pytest-orphan-sha-{uuid4()}",
            "message": "Orphan commit",
        },
    )

    assert response.status_code == 404
