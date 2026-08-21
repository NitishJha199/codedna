from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/incidents", tags=["incidents"])


class IncidentCreate(BaseModel):
    organization_id: UUID | None = None
    service_id: UUID | None = None
    environment_id: UUID | None = None
    deployment_id: UUID | None = None
    provider: str
    external_id: str
    title: str
    description: str | None = None
    severity: str
    status: str = "open"
    started_at: datetime
    detected_at: datetime | None = None
    mitigated_at: datetime | None = None
    resolved_at: datetime | None = None


class IncidentResponse(BaseModel):
    id: UUID
    organization_id: UUID | None
    service_id: UUID | None
    environment_id: UUID | None
    deployment_id: UUID | None
    provider: str
    external_id: str
    title: str
    description: str | None
    severity: str
    status: str
    started_at: datetime
    detected_at: datetime | None
    mitigated_at: datetime | None
    resolved_at: datetime | None


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident(
    payload: IncidentCreate,
    connection: Connection = Depends(connection_dependency),
) -> IncidentResponse:
    incident_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO incidents (
                    id, organization_id, service_id, environment_id, deployment_id,
                    provider, external_id, title, description, severity,
                    status, started_at, detected_at, mitigated_at, resolved_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id, organization_id, service_id, environment_id, deployment_id,
                    provider, external_id, title, description, severity,
                    status, started_at, detected_at, mitigated_at, resolved_at
                """,
                (
                    incident_id,
                    payload.organization_id,
                    payload.service_id,
                    payload.environment_id,
                    payload.deployment_id,
                    payload.provider,
                    payload.external_id,
                    payload.title,
                    payload.description,
                    payload.severity,
                    payload.status,
                    payload.started_at,
                    payload.detected_at,
                    payload.mitigated_at,
                    payload.resolved_at,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced organization, service, environment, or deployment does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incident with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Incident was not created.",
        )

    return IncidentResponse(
        id=row[0],
        organization_id=row[1],
        service_id=row[2],
        environment_id=row[3],
        deployment_id=row[4],
        provider=row[5],
        external_id=row[6],
        title=row[7],
        description=row[8],
        severity=row[9],
        status=row[10],
        started_at=row[11],
        detected_at=row[12],
        mitigated_at=row[13],
        resolved_at=row[14],
    )
