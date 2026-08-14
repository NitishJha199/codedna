from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    name: str
    provider: str | None = None
    external_id: str | None = None


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    provider: str | None
    external_id: str | None


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    payload: OrganizationCreate,
    connection: Connection = Depends(connection_dependency),
) -> OrganizationResponse:
    organization_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO organizations (
                    id,
                    name,
                    provider,
                    external_id
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id, name, provider, external_id
                """,
                (
                    organization_id,
                    payload.name,
                    payload.provider,
                    payload.external_id,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Organization was not created.",
        )

    return OrganizationResponse(
        id=row[0],
        name=row[1],
        provider=row[2],
        external_id=row[3],
    )
