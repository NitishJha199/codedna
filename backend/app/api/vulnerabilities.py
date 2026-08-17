from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(
    prefix="/vulnerabilities",
    tags=["vulnerabilities"],
)


class VulnerabilityCreate(BaseModel):
    provider: str
    external_id: str
    identifier: str
    severity: str | None = None
    summary: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    modified_at: datetime | None = None


class VulnerabilityResponse(BaseModel):
    id: UUID
    provider: str
    external_id: str
    identifier: str
    severity: str | None
    summary: str | None
    description: str | None
    published_at: datetime | None
    modified_at: datetime | None


@router.post(
    "",
    response_model=VulnerabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vulnerability(
    payload: VulnerabilityCreate,
    connection: Connection = Depends(connection_dependency),
) -> VulnerabilityResponse:
    vulnerability_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vulnerabilities (
                    id,
                    provider,
                    external_id,
                    identifier,
                    severity,
                    summary,
                    description,
                    published_at,
                    modified_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    provider,
                    external_id,
                    identifier,
                    severity,
                    summary,
                    description,
                    published_at,
                    modified_at
                """,
                (
                    vulnerability_id,
                    payload.provider,
                    payload.external_id,
                    payload.identifier,
                    payload.severity,
                    payload.summary,
                    payload.description,
                    payload.published_at,
                    payload.modified_at,
                ),
            )

            row = cursor.fetchone()

        connection.commit()

    except UniqueViolation:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vulnerability already exists.",
        )

    return VulnerabilityResponse(
        id=row[0],
        provider=row[1],
        external_id=row[2],
        identifier=row[3],
        severity=row[4],
        summary=row[5],
        description=row[6],
        published_at=row[7],
        modified_at=row[8],
    )
