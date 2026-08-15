from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/developers", tags=["developers"])


class DeveloperCreate(BaseModel):
    organization_id: UUID | None = None
    username: str | None = None
    display_name: str | None = None
    email: str | None = None
    provider: str | None = None
    external_id: str | None = None


class DeveloperResponse(BaseModel):
    id: UUID
    organization_id: UUID | None
    username: str | None
    display_name: str | None
    email: str | None
    provider: str | None
    external_id: str | None


@router.post(
    "",
    response_model=DeveloperResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_developer(
    payload: DeveloperCreate,
    connection: Connection = Depends(connection_dependency),
) -> DeveloperResponse:
    developer_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO developers (
                    id,
                    organization_id,
                    username,
                    display_name,
                    email,
                    provider,
                    external_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    organization_id,
                    username,
                    display_name,
                    email,
                    provider,
                    external_id
                """,
                (
                    developer_id,
                    payload.organization_id,
                    payload.username,
                    payload.display_name,
                    payload.email,
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
            detail="Developer with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Developer was not created.",
        )

    return DeveloperResponse(
        id=row[0],
        organization_id=row[1],
        username=row[2],
        display_name=row[3],
        email=row[4],
        provider=row[5],
        external_id=row[6],
    )
