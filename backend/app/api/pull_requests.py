from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


class PullRequestCreate(BaseModel):
    repository_id: UUID
    author_id: UUID | None = None
    provider: str
    external_id: str
    number: int | None = None
    title: str | None = None
    state: str = "open"
    source_branch: str | None = None
    target_branch: str | None = None


class PullRequestResponse(BaseModel):
    id: UUID
    repository_id: UUID
    author_id: UUID | None
    provider: str
    external_id: str
    number: int | None
    title: str | None
    state: str
    source_branch: str | None
    target_branch: str | None


@router.post(
    "",
    response_model=PullRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pull_request(
    payload: PullRequestCreate,
    connection: Connection = Depends(connection_dependency),
) -> PullRequestResponse:
    pull_request_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO pull_requests (
                    id,
                    repository_id,
                    author_id,
                    provider,
                    external_id,
                    number,
                    title,
                    state,
                    source_branch,
                    target_branch
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    repository_id,
                    author_id,
                    provider,
                    external_id,
                    number,
                    title,
                    state,
                    source_branch,
                    target_branch
                """,
                (
                    pull_request_id,
                    payload.repository_id,
                    payload.author_id,
                    payload.provider,
                    payload.external_id,
                    payload.number,
                    payload.title,
                    payload.state,
                    payload.source_branch,
                    payload.target_branch,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository or author does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Pull request with this provider/external_id or repository/number already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pull request was not created.",
        )

    return PullRequestResponse(
        id=row[0],
        repository_id=row[1],
        author_id=row[2],
        provider=row[3],
        external_id=row[4],
        number=row[5],
        title=row[6],
        state=row[7],
        source_branch=row[8],
        target_branch=row[9],
    )
