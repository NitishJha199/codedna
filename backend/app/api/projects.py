from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    organization_id: UUID
    name: str
    provider: str | None = None
    external_id: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    provider: str | None
    external_id: str | None


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    connection: Connection = Depends(connection_dependency),
) -> ProjectResponse:
    project_id = uuid4()

    try:
        with connection.cursor() as cursor:
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
                RETURNING id, organization_id, name, provider, external_id
                """,
                (
                    project_id,
                    payload.organization_id,
                    payload.name,
                    payload.provider,
                    payload.external_id,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this organization, provider, and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project was not created.",
        )

    return ProjectResponse(
        id=row[0],
        organization_id=row[1],
        name=row[2],
        provider=row[3],
        external_id=row[4],
    )
