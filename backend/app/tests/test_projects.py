from uuid import UUID, uuid4

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


def create_test_organization():
    organization_id = uuid4()

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO organizations (
                    id,
                    name,
                    provider,
                    external_id
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    organization_id,
                    "Projects Test Organization",
                    "pytest",
                    f"projects-org-{organization_id}",
                ),
            )
        connection.commit()

    return organization_id


def test_create_project():
    organization_id = create_test_organization()

    response = client.post(
        "/projects",
        json={
            "organization_id": str(organization_id),
            "name": "Pytest Project",
            "provider": "pytest",
            "external_id": f"pytest-project-{organization_id}",
        },
    )

    assert response.status_code == 201

    data = response.json()

    UUID(data["id"])
    assert data["organization_id"] == str(organization_id)
    assert data["name"] == "Pytest Project"
    assert data["provider"] == "pytest"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, organization_id, name, provider, external_id
                FROM projects
                WHERE id = %s
                """,
                (data["id"],),
            )
            row = cursor.fetchone()

    assert row is not None
    assert str(row[0]) == data["id"]
    assert str(row[1]) == str(organization_id)
    assert row[2] == "Pytest Project"
    assert row[3] == "pytest"


def test_duplicate_project_returns_conflict():
    organization_id = create_test_organization()

    payload = {
        "organization_id": str(organization_id),
        "name": "Duplicate Project",
        "provider": "pytest",
        "external_id": f"duplicate-project-{organization_id}",
    }

    first_response = client.post("/projects", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/projects", json=payload)

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": (
            "Project with this organization, provider, "
            "and external_id already exists."
        )
    }


def test_project_with_missing_organization_returns_not_found():
    response = client.post(
        "/projects",
        json={
            "organization_id": str(uuid4()),
            "name": "Orphan Project",
            "provider": "pytest",
            "external_id": f"orphan-project-{uuid4()}",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Organization does not exist."
    }
