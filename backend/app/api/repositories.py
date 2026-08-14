from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/repositories", tags=["repositories"])


class RepositoryCreate(BaseModel):
    project_id: UUID
    name: str
    provider: str
    external_id: str
    url: str | None = None


class RepositoryResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    provider: str
    external_id: str
    url: str | None


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_repository(
    payload: RepositoryCreate,
    connection: Connection = Depends(connection_dependency),
) -> RepositoryResponse:
    repository_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO repositories (
                    id,
                    project_id,
                    name,
                    provider,
                    external_id,
                    url
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    project_id,
                    name,
                    provider,
                    external_id,
                    url
                """,
                (
                    repository_id,
                    payload.project_id,
                    payload.name,
                    payload.provider,
                    payload.external_id,
                    payload.url,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Repository with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Repository was not created.",
        )

    return RepositoryResponse(
        id=row[0],
        project_id=row[1],
        name=row[2],
        provider=row[3],
        external_id=row[4],
        url=row[5],
    )
