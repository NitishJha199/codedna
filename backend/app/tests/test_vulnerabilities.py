from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_vulnerability():
    response = client.post(
        "/vulnerabilities",
        json={
            "provider": "pytest",
            "external_id": "vulnerability-test-001",
            "identifier": "CVE-2026-TEST-001",
            "severity": "high",
            "summary": "Test vulnerability",
            "description": "Test vulnerability description",
        },
    )

    assert response.status_code == 201
    assert response.json()["identifier"] == "CVE-2026-TEST-001"


def test_duplicate_vulnerability_provider_external_id_returns_conflict():
    payload = {
        "provider": "pytest",
        "external_id": "vulnerability-duplicate-001",
        "identifier": "CVE-2026-TEST-002",
    }

    first = client.post("/vulnerabilities", json=payload)
    second = client.post("/vulnerabilities", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_duplicate_vulnerability_identifier_returns_conflict():
    first = client.post(
        "/vulnerabilities",
        json={
            "provider": "pytest",
            "external_id": "vulnerability-identifier-001",
            "identifier": "CVE-2026-TEST-003",
        },
    )

    second = client.post(
        "/vulnerabilities",
        json={
            "provider": "another-provider",
            "external_id": "vulnerability-identifier-002",
            "identifier": "CVE-2026-TEST-003",
        },
    )

    assert first.status_code == 201
    assert second.status_code == 409
