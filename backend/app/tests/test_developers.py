from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_developer():
    response = client.post(
        "/developers",
        json={
            "username": "alice",
            "display_name": "Alice Developer",
            "email": "alice@example.com",
            "provider": "pytest",
            "external_id": f"developer-{uuid4()}",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"]
    assert body["organization_id"] is None
    assert body["username"] == "alice"
    assert body["display_name"] == "Alice Developer"
    assert body["email"] == "alice@example.com"
    assert body["provider"] == "pytest"


def test_create_developer_with_organization():
    organization_response = client.post(
        "/organizations",
        json={
            "name": "Developer Test Organization",
            "provider": "pytest",
            "external_id": f"developer-org-{uuid4()}",
        },
    )

    assert organization_response.status_code == 201

    organization_id = organization_response.json()["id"]

    response = client.post(
        "/developers",
        json={
            "organization_id": organization_id,
            "username": "bob",
            "display_name": "Bob Developer",
            "provider": "pytest",
            "external_id": f"developer-{uuid4()}",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["organization_id"] == organization_id
    assert body["username"] == "bob"
    assert body["display_name"] == "Bob Developer"


def test_duplicate_developer_returns_conflict():
    payload = {
        "username": "duplicate-user",
        "display_name": "Duplicate Developer",
        "provider": "pytest",
        "external_id": f"duplicate-developer-{uuid4()}",
    }

    first_response = client.post("/developers", json=payload)

    assert first_response.status_code == 201

    second_response = client.post(
        "/developers",
        json={
            **payload,
            "display_name": "Duplicate Developer Again",
        },
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Developer with this provider and external_id already exists."
    )


def test_nonexistent_organization_returns_not_found():
    response = client.post(
        "/developers",
        json={
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "username": "orphan-user",
            "provider": "pytest",
            "external_id": f"orphan-developer-{uuid4()}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Organization does not exist."
