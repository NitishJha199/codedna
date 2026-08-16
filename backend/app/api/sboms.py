from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.types.json import Jsonb
from psycopg.errors import ForeignKeyViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/sboms", tags=["sboms"])


class SBOMCreate(BaseModel):
    artifact_id: UUID | None = None
    container_image_id: UUID | None = None
    format: str
    version: str | None = None
    digest: str | None = None
    generated_at: datetime | None = None
    payload: dict[str, Any] | None = None


class SBOMResponse(BaseModel):
    id: UUID
    artifact_id: UUID | None
    container_image_id: UUID | None
    format: str
    version: str | None
    digest: str | None
    generated_at: datetime | None
    payload: dict[str, Any] | None


@router.post(
    "",
    response_model=SBOMResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sbom(
    payload: SBOMCreate,
    connection: Connection = Depends(connection_dependency),
) -> SBOMResponse:
    sbom_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sboms (
                    id,
                    artifact_id,
                    container_image_id,
                    format,
                    version,
                    digest,
                    generated_at,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    artifact_id,
                    container_image_id,
                    format,
                    version,
                    digest,
                    generated_at,
                    payload
                """,
                (
                    sbom_id,
                    payload.artifact_id,
                    payload.container_image_id,
                    payload.format,
                    payload.version,
                    payload.digest,
                    payload.generated_at,
                    Jsonb(payload.payload) if payload.payload is not None else None,
                ),
            )

            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced artifact or container image not found.",
        )

    return SBOMResponse(
        id=row[0],
        artifact_id=row[1],
        container_image_id=row[2],
        format=row[3],
        version=row[4],
        digest=row[5],
        generated_at=row[6],
        payload=row[7],
    )
