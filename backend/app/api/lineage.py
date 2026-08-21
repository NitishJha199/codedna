from typing import Any
from fastapi import APIRouter, HTTPException, status
from backend.app.graph.queries import (
    get_deployment_lineage,
    get_vulnerability_impact,
    get_developer_impact,
)

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


@router.get("/vulnerabilities/{vulnerability_id}")
def read_vulnerability_impact(vulnerability_id: str) -> dict[str, Any]:
    impact = get_vulnerability_impact(vulnerability_id)
    if not impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vulnerability impact for '{vulnerability_id}' not found",
        )
    return impact


@router.get("/developers/{developer_id}")
def read_developer_impact(developer_id: str) -> dict[str, Any]:
    impact = get_developer_impact(developer_id)
    if not impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Developer impact for '{developer_id}' not found",
        )
    return impact
