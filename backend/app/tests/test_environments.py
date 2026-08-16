import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_environment():
    response = client.post(
        "/environments",
        json={
            "name": "production",
            "environment_type": "production",
            "provider": "pytest",
            "external_id": "environment-test-001",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "production"
    assert response.json()["environment_type"] == "production"


def test_duplicate_environment_returns_conflict():
    payload = {
        "name": "staging",
        "environment_type": "staging",
        "provider": "pytest",
        "external_id": "environment-duplicate-001",
    }

    first = client.post("/environments", json=payload)
    second = client.post("/environments", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_environment_with_nonexistent_organization_returns_not_found():
    response = client.post(
        "/environments",
        json={
            "organization_id": str(uuid.uuid4()),
            "name": "orphan-environment",
        },
    )

    assert response.status_code == 404
