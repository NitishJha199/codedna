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


def create_test_project() -> str:
    organization_id = uuid4()
    project_id = uuid4()

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
                    "Repository Test Organization",
                    "pytest",
                    f"repo-test-org-{organization_id}",
                ),
            )

            cursor.execute(
                """
                INSERT INTO projects (
                    id,
                    organization_id,
                    name,
                    provider,
                    external_id
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    project_id,
                    organization_id,
                    "Repository Test Project",
                    "pytest",
                    f"repo-test-project-{project_id}",
                ),
            )

        connection.commit()

    return str(project_id)


def test_create_repository():
    project_id = create_test_project()
    external_id = f"pytest-repository-{uuid4()}"

    response = client.post(
        "/repositories",
        json={
            "project_id": project_id,
            "name": "Pytest Repository",
            "provider": "pytest",
            "external_id": external_id,
            "url": "https://example.com/pytest/repository",
        },
    )

    assert response.status_code == 201

    data = response.json()

    UUID(data["id"])
    assert data["project_id"] == project_id
    assert data["name"] == "Pytest Repository"
    assert data["provider"] == "pytest"
    assert data["external_id"] == external_id
    assert data["url"] == "https://example.com/pytest/repository"

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    project_id,
                    name,
                    provider,
                    external_id,
                    url
                FROM repositories
                WHERE id = %s
                """,
                (data["id"],),
            )
            row = cursor.fetchone()

    assert row is not None
    assert str(row[0]) == data["id"]
    assert str(row[1]) == project_id
    assert row[2] == "Pytest Repository"
    assert row[3] == "pytest"
    assert row[4] == external_id
    assert row[5] == "https://example.com/pytest/repository"


def test_duplicate_repository_returns_conflict():
    project_id = create_test_project()
    external_id = f"pytest-duplicate-repository-{uuid4()}"

    payload = {
        "project_id": project_id,
        "name": "Pytest Duplicate Repository",
        "provider": "pytest",
        "external_id": external_id,
    }

    first_response = client.post("/repositories", json=payload)

    assert first_response.status_code == 201

    second_response = client.post("/repositories", json=payload)

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Repository with this provider and external_id already exists."
    }


def test_repository_with_missing_project_returns_not_found():
    response = client.post(
        "/repositories",
        json={
            "project_id": "00000000-0000-0000-0000-000000000000",
            "name": "Orphan Repository",
            "provider": "pytest",
            "external_id": f"pytest-orphan-{uuid4()}",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Project does not exist."
    }
