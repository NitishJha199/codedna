from datetime import datetime
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from psycopg import Connection

from backend.app.analytics.dora import get_dora_metrics
from backend.app.db.postgres import connection_dependency

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dora")
def read_dora_metrics(
    start_time: datetime | None = Query(None, description="Start time ISO format"),
    end_time: datetime | None = Query(None, description="End time ISO format"),
    environment_id: UUID | None = Query(None, description="Filter by environment ID"),
    service_id: UUID | None = Query(None, description="Filter by service ID"),
    connection: Connection = Depends(connection_dependency),
) -> dict[str, Any]:
    return get_dora_metrics(
        connection=connection,
        start_time=start_time,
        end_time=end_time,
        environment_id=environment_id,
        service_id=service_id,
    )
