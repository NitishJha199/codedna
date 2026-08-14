from uuid import UUID

import psycopg
from fastapi.testclient import TestClient

from app.main import app
from backend.app.core.config import settings


client = TestClient(app)


def get_connection():
    return psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def test_create_organization():
    response = client.post(
        "/organizations",
        json={
            "name": "Pytest Organization",
            "provider": "pytest",
            "external_id": "pytest-org-001",
        },
    )

    assert response.status_code == 201

    data = response.json()

    UUID(data["id"])
    assert data["name"] == "Pytest Organization"
    assert data["provider"] == "pytest"
    assert data["external_id"] == "pytest-org-001"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, provider, external_id
                FROM organizations
                WHERE id = %s
                """,
                (data["id"],),
            )
            row = cursor.fetchone()

    assert row is not None
    assert str(row[0]) == data["id"]
    assert row[1] == "Pytest Organization"
    assert row[2] == "pytest"
    assert row[3] == "pytest-org-001"


def test_duplicate_organization_returns_conflict():
    payload = {
        "name": "Pytest Duplicate Organization",
        "provider": "pytest",
        "external_id": "pytest-org-duplicate-001",
    }

    first_response = client.post("/organizations", json=payload)

    assert first_response.status_code == 201

    second_response = client.post("/organizations", json=payload)

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Organization with this provider and external_id already exists."
    }
