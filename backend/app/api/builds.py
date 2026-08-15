from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/builds", tags=["builds"])


class BuildCreate(BaseModel):
    pipeline_id: UUID
    provider: str
    external_id: str
    commit_id: UUID | None = None
    status: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class BuildResponse(BaseModel):
    id: UUID
    pipeline_id: UUID
    commit_id: UUID | None
    provider: str
    external_id: str
    status: str | None
    started_at: datetime | None
    finished_at: datetime | None


@router.post(
    "",
    response_model=BuildResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_build(
    payload: BuildCreate,
    connection: Connection = Depends(connection_dependency),
) -> BuildResponse:
    build_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO builds (
                    id,
                    pipeline_id,
                    commit_id,
                    provider,
                    external_id,
                    status,
                    started_at,
                    finished_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    pipeline_id,
                    commit_id,
                    provider,
                    external_id,
                    status,
                    started_at,
                    finished_at
                """,
                (
                    build_id,
                    payload.pipeline_id,
                    payload.commit_id,
                    payload.provider,
                    payload.external_id,
                    payload.status,
                    payload.started_at,
                    payload.finished_at,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline or commit does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Build with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Build was not created.",
        )

    return BuildResponse(
        id=row[0],
        pipeline_id=row[1],
        commit_id=row[2],
        provider=row[3],
        external_id=row[4],
        status=row[5],
        started_at=row[6],
        finished_at=row[7],
    )
