from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation, UniqueViolation

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/container-images", tags=["container-images"])


class ContainerImageCreate(BaseModel):
    artifact_id: UUID | None = None
    repository_id: UUID | None = None
    registry: str
    image_name: str
    tag: str | None = None
    digest: str | None = None


class ContainerImageResponse(BaseModel):
    id: UUID
    artifact_id: UUID | None
    repository_id: UUID | None
    registry: str
    image_name: str
    tag: str | None
    digest: str | None


@router.post("", response_model=ContainerImageResponse, status_code=status.HTTP_201_CREATED)
def create_container_image(
    payload: ContainerImageCreate,
    connection: Connection = Depends(connection_dependency),
) -> ContainerImageResponse:
    image_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO container_images (
                    id, artifact_id, repository_id, registry,
                    image_name, tag, digest
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id, artifact_id, repository_id, registry,
                    image_name, tag, digest
                """,
                (
                    image_id,
                    payload.artifact_id,
                    payload.repository_id,
                    payload.registry,
                    payload.image_name,
                    payload.tag,
                    payload.digest,
                ),
            )
            row = cursor.fetchone()

        connection.commit()

    except ForeignKeyViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact or repository does not exist.",
        ) from exc

    except UniqueViolation as exc:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Container image with this registry, image_name, and digest already exists.",
        ) from exc

    if row is None:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Container image was not created.",
        )

    return ContainerImageResponse(
        id=row[0],
        artifact_id=row[1],
        repository_id=row[2],
        registry=row[3],
        image_name=row[4],
        tag=row[5],
        digest=row[6],
    )
