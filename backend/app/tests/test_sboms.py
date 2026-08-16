import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_sbom():
    response = client.post(
        "/sboms",
        json={
            "format": "cyclonedx",
            "version": "1.5",
            "digest": "sha256:sbom-test-001",
            "payload": {
                "bomFormat": "CycloneDX",
                "specVersion": "1.5",
                "components": [],
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["format"] == "cyclonedx"


def test_create_sbom_with_nonexistent_artifact_returns_not_found():
    response = client.post(
        "/sboms",
        json={
            "artifact_id": str(uuid.uuid4()),
            "format": "cyclonedx",
            "version": "1.5",
        },
    )

    assert response.status_code == 404


def test_create_sbom_with_nonexistent_container_image_returns_not_found():
    response = client.post(
        "/sboms",
        json={
            "container_image_id": str(uuid.uuid4()),
            "format": "spdx",
            "version": "2.3",
        },
    )

    assert response.status_code == 404
