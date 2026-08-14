from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/commits", tags=["commits"])


class CommitCreate(BaseModel):
    repository_id: UUID
    developer_id: UUID | None = None
    provider: str
    external_id: str
    sha: str
    message: str | None = None
    occurred_at: datetime | None = None


class CommitResponse(BaseModel):
    id: UUID
    repository_id: UUID
    developer_id: UUID | None
    provider: str
    external_id: str
    sha: str
    message: str | None
    occurred_at: datetime | None


@router.post(
    "",
    response_model=CommitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_commit(
    payload: CommitCreate,
    connection: Connection = Depends(connection_dependency),
) -> CommitResponse:
    commit_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO commits (
                    id,
                    repository_id,
                    developer_id,
                    provider,
                    external_id,
                    sha,
                    message,
                    occurred_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    repository_id,
                    developer_id,
                    provider,
                    external_id,
                    sha,
                    message,
                    occurred_at
                """,
                (
                    commit_id,
                    payload.repository_id,
                    payload.developer_id,
                    payload.provider,
                    payload.external_id,
                    payload.sha,
                    payload.message,
                    payload.occurred_at,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository or developer does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Commit with this provider and external_id or repository and sha already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Commit was not created.",
        )

    return CommitResponse(
        id=row[0],
        repository_id=row[1],
        developer_id=row[2],
        provider=row[3],
        external_id=row[4],
        sha=row[5],
        message=row[6],
        occurred_at=row[7],
    )
