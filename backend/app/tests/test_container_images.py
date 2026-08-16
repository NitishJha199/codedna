from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_container_image():
    response = client.post(
        "/container-images",
        json={
            "registry": "docker.io",
            "image_name": "codedna/test",
            "tag": "latest",
        },
    )

    assert response.status_code == 201
    assert response.json()["image_name"] == "codedna/test"


def test_duplicate_container_image_returns_conflict():
    payload = {
        "registry": "pytest-registry",
        "image_name": "codedna/duplicate",
        "digest": "sha256:duplicate-test-001",
    }

    first = client.post("/container-images", json=payload)
    second = client.post("/container-images", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
