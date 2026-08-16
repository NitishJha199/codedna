from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_artifact():
    response = client.post(
        "/artifacts",
        json={
            "name": "codedna-artifact",
            "version": "1.0.0",
            "artifact_type": "package",
            "provider": "pytest",
            "external_id": "artifact-test-001",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "codedna-artifact"


def test_duplicate_artifact_returns_conflict():
    payload = {
        "name": "duplicate-artifact",
        "provider": "pytest",
        "external_id": "artifact-duplicate-001",
    }

    first = client.post("/artifacts", json=payload)
    second = client.post("/artifacts", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
