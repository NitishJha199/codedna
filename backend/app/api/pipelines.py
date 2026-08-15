from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


class PipelineCreate(BaseModel):
    repository_id: UUID
    provider: str
    external_id: str
    name: str | None = None
    status: str | None = None
    branch: str | None = None
    commit_id: UUID | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class PipelineResponse(BaseModel):
    id: UUID
    repository_id: UUID
    provider: str
    external_id: str
    name: str | None
    status: str | None
    branch: str | None
    commit_id: UUID | None
    started_at: datetime | None
    finished_at: datetime | None


@router.post(
    "",
    response_model=PipelineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pipeline(
    payload: PipelineCreate,
    connection: Connection = Depends(connection_dependency),
) -> PipelineResponse:
    pipeline_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pipelines (
                    id,
                    repository_id,
                    provider,
                    external_id,
                    name,
                    status,
                    branch,
                    commit_id,
                    started_at,
                    finished_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    repository_id,
                    provider,
                    external_id,
                    name,
                    status,
                    branch,
                    commit_id,
                    started_at,
                    finished_at
                """,
                (
                    pipeline_id,
                    payload.repository_id,
                    payload.provider,
                    payload.external_id,
                    payload.name,
                    payload.status,
                    payload.branch,
                    payload.commit_id,
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
            detail="Repository or commit does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pipeline with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline was not created.",
        )

    return PipelineResponse(
        id=row[0],
        repository_id=row[1],
        provider=row[2],
        external_id=row[3],
        name=row[4],
        status=row[5],
        branch=row[6],
        commit_id=row[7],
        started_at=row[8],
        finished_at=row[9],
    )
