from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/environments", tags=["environments"])


class EnvironmentCreate(BaseModel):
    organization_id: UUID | None = None
    name: str
    environment_type: str | None = None
    provider: str | None = None
    external_id: str | None = None


class EnvironmentResponse(BaseModel):
    id: UUID
    organization_id: UUID | None
    name: str
    environment_type: str | None
    provider: str | None
    external_id: str | None


@router.post(
    "",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_environment(
    payload: EnvironmentCreate,
    connection: Connection = Depends(connection_dependency),
) -> EnvironmentResponse:
    environment_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO environments (
                    id, organization_id, name, environment_type,
                    provider, external_id
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING
                    id, organization_id, name, environment_type,
                    provider, external_id
                """,
                (
                    environment_id,
                    payload.organization_id,
                    payload.name,
                    payload.environment_type,
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
            detail="Environment with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Environment was not created.",
        )

    return EnvironmentResponse(
        id=row[0],
        organization_id=row[1],
        name=row[2],
        environment_type=row[3],
        provider=row[4],
        external_id=row[5],
    )
