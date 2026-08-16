import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def create_test_environment():
    response = client.post(
        "/environments",
        json={
            "name": "pytest-deployment-env",
            "provider": "pytest",
            "external_id": "deployment-env-001",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_test_service():
    response = client.post(
        "/services",
        json={
            "name": "pytest-deployment-service",
            "provider": "pytest",
            "external_id": "deployment-service-001",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_deployment():
    environment_id = create_test_environment()
    service_id = create_test_service()

    response = client.post(
        "/deployments",
        json={
            "environment_id": environment_id,
            "service_id": service_id,
            "provider": "pytest",
            "external_id": "deployment-test-001",
            "status": "success",
        },
    )

    assert response.status_code == 201
    assert response.json()["provider"] == "pytest"
    assert response.json()["external_id"] == "deployment-test-001"
    assert response.json()["status"] == "success"


def test_duplicate_deployment_returns_conflict():
    environment_id = create_test_environment()
    service_id = create_test_service()

    payload = {
        "environment_id": environment_id,
        "service_id": service_id,
        "provider": "pytest",
        "external_id": "deployment-duplicate-001",
        "status": "success",
    }

    first = client.post("/deployments", json=payload)
    second = client.post("/deployments", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_deployment_with_nonexistent_environment_returns_not_found():
    service_id = create_test_service()

    response = client.post(
        "/deployments",
        json={
            "environment_id": str(uuid.uuid4()),
            "service_id": service_id,
            "provider": "pytest",
            "external_id": "deployment-invalid-env-001",
        },
    )

    assert response.status_code == 404


def test_deployment_with_nonexistent_service_returns_not_found():
    environment_id = create_test_environment()

    response = client.post(
        "/deployments",
        json={
            "environment_id": environment_id,
            "service_id": str(uuid.uuid4()),
            "provider": "pytest",
            "external_id": "deployment-invalid-service-001",
        },
    )

    assert response.status_code == 404
