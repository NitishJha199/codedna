from backend.app.events.processor import process_pending_events
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    provider: str
    event_type: str
    external_event_id: str | None = None
    idempotency_key: str
    source_occurred_at: datetime | None = None
    payload: dict[str, Any]
    processing_status: str = "pending"
    processed_at: datetime | None = None
    error_message: str | None = None


class EventResponse(BaseModel):
    id: UUID
    provider: str
    event_type: str
    external_event_id: str | None
    idempotency_key: str
    source_occurred_at: datetime | None
    processing_status: str
    processed_at: datetime | None
    error_message: str | None
    payload: dict[str, Any]


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    payload: EventCreate,
    connection: Connection = Depends(connection_dependency),
) -> EventResponse:
    event_id = uuid4()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO events (
                    id,
                    provider,
                    event_type,
                    external_event_id,
                    idempotency_key,
                    source_occurred_at,
                    payload,
                    processing_status,
                    processed_at,
                    error_message
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                RETURNING
                    id,
                    provider,
                    event_type,
                    external_event_id,
                    idempotency_key,
                    source_occurred_at,
                    processing_status,
                    processed_at,
                    error_message,
                    payload
                """,
                (
                    event_id,
                    payload.provider,
                    payload.event_type,
                    payload.external_event_id,
                    payload.idempotency_key,
                    payload.source_occurred_at,
                    Jsonb(payload.payload),
                    payload.processing_status,
                    payload.processed_at,
                    payload.error_message,
                ),
            )

            row = cursor.fetchone()

        connection.commit()

    except UniqueViolation:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event with this idempotency key already exists.",
        )

    return EventResponse(
        id=row[0],
        provider=row[1],
        event_type=row[2],
        external_event_id=row[3],
        idempotency_key=row[4],
        source_occurred_at=row[5],
        processing_status=row[6],
        processed_at=row[7],
        error_message=row[8],
        payload=row[9],
    )


@router.post("/process-pending")
def process_pending(
    batch_size: int = 50,
    connection: Connection = Depends(connection_dependency),
) -> dict[str, int]:
    return process_pending_events(connection, batch_size=batch_size, sync_graph=True)
