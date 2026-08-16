from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


class ArtifactCreate(BaseModel):
    build_id: UUID | None = None
    repository_id: UUID | None = None
    provider: str | None = None
    external_id: str | None = None
    name: str
    version: str | None = None
    artifact_type: str | None = None
    digest: str | None = None


class ArtifactResponse(BaseModel):
    id: UUID
    build_id: UUID | None
    repository_id: UUID | None
    provider: str | None
    external_id: str | None
    name: str
    version: str | None
    artifact_type: str | None
    digest: str | None


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
def create_artifact(
    payload: ArtifactCreate,
    connection: Connection = Depends(connection_dependency),
) -> ArtifactResponse:
    artifact_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO artifacts (
                    id, build_id, repository_id, provider, external_id,
                    name, version, artifact_type, digest
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id, build_id, repository_id, provider, external_id,
                    name, version, artifact_type, digest
                """,
                (
                    artifact_id,
                    payload.build_id,
                    payload.repository_id,
                    payload.provider,
                    payload.external_id,
                    payload.name,
                    payload.version,
                    payload.artifact_type,
                    payload.digest,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build or repository does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Artifact with this provider and external_id already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Artifact was not created.",
        )

    return ArtifactResponse(
        id=row[0],
        build_id=row[1],
        repository_id=row[2],
        provider=row[3],
        external_id=row[4],
        name=row[5],
        version=row[6],
        artifact_type=row[7],
        digest=row[8],
    )
