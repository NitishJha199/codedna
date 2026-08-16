from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/dependencies", tags=["dependencies"])


class DependencyCreate(BaseModel):
    repository_id: UUID
    name: str
    version: str | None = None
    package_manager: str | None = None
    provider: str | None = None
    external_id: str | None = None


class DependencyResponse(BaseModel):
    id: UUID
    repository_id: UUID
    name: str
    version: str | None
    package_manager: str | None
    provider: str | None
    external_id: str | None


@router.post("", response_model=DependencyResponse, status_code=status.HTTP_201_CREATED)
def create_dependency(
    payload: DependencyCreate,
    connection: Connection = Depends(connection_dependency),
) -> DependencyResponse:
    dependency_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO dependencies (
                    id, repository_id, name, version,
                    package_manager, provider, external_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id, repository_id, name, version,
                    package_manager, provider, external_id
                """,
                (
                    dependency_id,
                    payload.repository_id,
                    payload.name,
                    payload.version,
                    payload.package_manager,
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
            detail="Repository does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dependency with this repository, name, version, and package_manager already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependency was not created.",
        )

    return DependencyResponse(*row)
