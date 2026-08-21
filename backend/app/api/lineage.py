from typing import Any
from fastapi import APIRouter, HTTPException, status
from backend.app.graph.queries import get_deployment_lineage

router = APIRouter(prefix="/lineage", tags=["lineage"])


@router.get("/deployments/{deployment_id}")
def read_deployment_lineage(deployment_id: str) -> dict[str, Any]:
    lineage = get_deployment_lineage(deployment_id)
    if not lineage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lineage for deployment '{deployment_id}' not found",
        )
    return lineage
