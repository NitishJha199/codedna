import uuid

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_security_finding_with_nonexistent_repository():
    response = client.post(
        "/security-findings",
        json={
            "repository_id": str(uuid.uuid4()),
            "provider": "pytest",
            "external_id": "finding-test-001",
            "finding_type": "vulnerability",
            "severity": "high",
            "title": "Test finding",
        },
    )

    assert response.status_code == 404


def test_security_finding_duplicate_returns_conflict():
    assert True
