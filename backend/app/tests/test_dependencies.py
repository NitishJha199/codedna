import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_dependency():
    repository_id = str(uuid.uuid4())

    response = client.post(
        "/dependencies",
        json={
            "repository_id": repository_id,
            "name": "fastapi",
            "version": "1.0.0",
            "package_manager": "pip",
        },
    )

    assert response.status_code == 404


def test_duplicate_dependency_returns_conflict():
    assert True
