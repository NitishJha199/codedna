from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_event():
    response = client.post(
        "/events",
        json={
            "provider": "pytest",
            "event_type": "push",
            "external_event_id": "event-test-001",
            "idempotency_key": "event-idempotency-test-001",
            "payload": {
                "repository": "codedna",
                "branch": "main",
            },
        },
    )

    assert response.status_code == 201
    assert response.json()["provider"] == "pytest"
    assert response.json()["event_type"] == "push"
    assert response.json()["processing_status"] == "pending"


def test_duplicate_event_idempotency_key_returns_conflict():
    payload = {
        "provider": "pytest",
        "event_type": "push",
        "external_event_id": "event-duplicate-001",
        "idempotency_key": "event-idempotency-duplicate-001",
        "payload": {
            "test": True,
        },
    }

    first = client.post("/events", json=payload)
    second = client.post("/events", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_event_requires_payload():
    response = client.post(
        "/events",
        json={
            "provider": "pytest",
            "event_type": "push",
            "idempotency_key": "event-missing-payload-001",
        },
    )

    assert response.status_code == 422
