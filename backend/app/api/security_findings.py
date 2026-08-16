from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/security-findings", tags=["security-findings"])


class SecurityFindingCreate(BaseModel):
    repository_id: UUID
    dependency_id: UUID | None = None
    vulnerability_id: UUID | None = None
    provider: str
    external_id: str | None = None
    finding_type: str
    severity: str | None = None
    status: str = "open"
    title: str | None = None
    description: str | None = None
    detected_at: datetime | None = None
    resolved_at: datetime | None = None


class SecurityFindingResponse(BaseModel):
    id: UUID
    repository_id: UUID
    dependency_id: UUID | None
    vulnerability_id: UUID | None
    provider: str
    external_id: str | None
    finding_type: str
    severity: str | None
    status: str
    title: str | None
    description: str | None
    detected_at: datetime | None
    resolved_at: datetime | None


@router.post("", response_model=SecurityFindingResponse, status_code=status.HTTP_201_CREATED)
def create_security_finding(
    payload: SecurityFindingCreate,
    connection: Connection = Depends(connection_dependency),
) -> SecurityFindingResponse:
    finding_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO security_findings (
                    id, repository_id, dependency_id, vulnerability_id,
                    provider, external_id, finding_type, severity,
                    status, title, description, detected_at, resolved_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                RETURNING
                    id, repository_id, dependency_id, vulnerability_id,
                    provider, external_id, finding_type, severity,
                    status, title, description, detected_at, resolved_at
                """,
                (
                    finding_id,
                    payload.repository_id,
                    payload.dependency_id,
                    payload.vulnerability_id,
                    payload.provider,
                    payload.external_id,
                    payload.finding_type,
                    payload.severity,
                    payload.status,
                    payload.title,
                    payload.description,
                    payload.detected_at,
                    payload.resolved_at,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository, dependency, or vulnerability does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Security finding with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security finding was not created.",
        )

    return SecurityFindingResponse(*row)
