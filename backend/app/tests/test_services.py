import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_service():
    response = client.post(
        "/services",
        json={
            "name": "codedna-api",
            "provider": "pytest",
            "external_id": "service-test-001",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "codedna-api"


def test_duplicate_service_returns_conflict():
    payload = {
        "name": "codedna-worker",
        "provider": "pytest",
        "external_id": "service-duplicate-001",
    }

    first = client.post("/services", json=payload)
    second = client.post("/services", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_service_with_nonexistent_organization_returns_not_found():
    response = client.post(
        "/services",
        json={
            "organization_id": str(uuid.uuid4()),
            "name": "orphan-service",
        },
    )

    assert response.status_code == 404
