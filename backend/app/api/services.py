from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/services", tags=["services"])


class ServiceCreate(BaseModel):
    organization_id: UUID | None = None
    name: str
    provider: str | None = None
    external_id: str | None = None


class ServiceResponse(BaseModel):
    id: UUID
    organization_id: UUID | None
    name: str
    provider: str | None
    external_id: str | None


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    payload: ServiceCreate,
    connection: Connection = Depends(connection_dependency),
) -> ServiceResponse:
    service_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO services (
                    id,
                    organization_id,
                    name,
                    provider,
                    external_id
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING
                    id,
                    organization_id,
                    name,
                    provider,
                    external_id
                """,
                (
                    service_id,
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
            detail="Service with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service was not created.",
        )

    return ServiceResponse(
        id=row[0],
        organization_id=row[1],
        name=row[2],
        provider=row[3],
        external_id=row[4],
    )
