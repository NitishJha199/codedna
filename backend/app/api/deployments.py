from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/deployments", tags=["deployments"])


class DeploymentCreate(BaseModel):
    environment_id: UUID
    service_id: UUID
    artifact_id: UUID | None = None
    container_image_id: UUID | None = None
    provider: str
    external_id: str
    status: str | None = None
    deployed_at: datetime | None = None


class DeploymentResponse(BaseModel):
    id: UUID
    environment_id: UUID
    service_id: UUID
    artifact_id: UUID | None
    container_image_id: UUID | None
    provider: str
    external_id: str
    status: str | None
    deployed_at: datetime | None


@router.post(
    "",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_deployment(
    payload: DeploymentCreate,
    connection: Connection = Depends(connection_dependency),
) -> DeploymentResponse:
    deployment_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO deployments (
                    id,
                    environment_id,
                    service_id,
                    artifact_id,
                    container_image_id,
                    provider,
                    external_id,
                    status,
                    deployed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    environment_id,
                    service_id,
                    artifact_id,
                    container_image_id,
                    provider,
                    external_id,
                    status,
                    deployed_at
                """,
                (
                    deployment_id,
                    payload.environment_id,
                    payload.service_id,
                    payload.artifact_id,
                    payload.container_image_id,
                    payload.provider,
                    payload.external_id,
                    payload.status,
                    payload.deployed_at,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced resource does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deployment with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deployment was not created.",
        )

    return DeploymentResponse(
        id=row[0],
        environment_id=row[1],
        service_id=row[2],
        artifact_id=row[3],
        container_image_id=row[4],
        provider=row[5],
        external_id=row[6],
        status=row[7],
        deployed_at=row[8],
    )
