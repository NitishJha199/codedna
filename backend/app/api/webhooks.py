import json
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from psycopg import Connection
from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from backend.app.core.config import settings
from backend.app.db.postgres import connection_dependency
from backend.app.webhooks.security import verify_github_signature, verify_gitlab_token

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/github", status_code=status.HTTP_202_ACCEPTED)
async def receive_github_webhook(
    request: Request,
    x_github_event: str | None = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: str | None = Header(None, alias="X-GitHub-Delivery"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
    connection: Connection = Depends(connection_dependency),
) -> dict[str, str]:
    if not x_github_event or not x_github_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required GitHub headers (X-GitHub-Event, X-GitHub-Delivery).",
        )

    raw_body = await request.body()

    if settings.github_webhook_secret:
        if not verify_github_signature(raw_body, x_hub_signature_256, settings.github_webhook_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature.",
            )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        payload = {}

    idempotency_key = f"github:{x_github_delivery}"
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
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                """,
                (
                    event_id,
                    "github",
                    x_github_event,
                    x_github_delivery,
                    idempotency_key,
                    datetime.now(timezone.utc),
                    Jsonb(payload),
                ),
            )
        connection.commit()
    except UniqueViolation:
        connection.rollback()
        return {"status": "duplicate", "message": "Event already recorded", "idempotency_key": idempotency_key}

    return {"status": "accepted", "event_id": str(event_id), "idempotency_key": idempotency_key}


@router.post("/gitlab", status_code=status.HTTP_202_ACCEPTED)
async def receive_gitlab_webhook(
    request: Request,
    x_gitlab_event: str | None = Header(None, alias="X-Gitlab-Event"),
    x_gitlab_token: str | None = Header(None, alias="X-Gitlab-Token"),
    x_gitlab_event_uuid: str | None = Header(None, alias="X-Gitlab-Event-UUID"),
    connection: Connection = Depends(connection_dependency),
) -> dict[str, str]:
    if not x_gitlab_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required GitLab header (X-Gitlab-Event).",
        )

    if settings.gitlab_webhook_secret:
        if not verify_gitlab_token(x_gitlab_token, settings.gitlab_webhook_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid GitLab webhook token.",
            )

    raw_body = await request.body()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        payload = {}

    external_id = x_gitlab_event_uuid or payload.get("object_attributes", {}).get("id") or str(uuid4())
    idempotency_key = f"gitlab:{external_id}"
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
                    processing_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                """,
                (
                    event_id,
                    "gitlab",
                    x_gitlab_event,
                    str(external_id),
                    idempotency_key,
                    datetime.now(timezone.utc),
                    Jsonb(payload),
                ),
            )
        connection.commit()
    except UniqueViolation:
        connection.rollback()
        return {"status": "duplicate", "message": "Event already recorded", "idempotency_key": idempotency_key}

    return {"status": "accepted", "event_id": str(event_id), "idempotency_key": idempotency_key}
