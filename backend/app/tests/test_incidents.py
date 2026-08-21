import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_incident_nonexistent_service():
    response = client.post(
        "/incidents",
        json={
            "service_id": str(uuid.uuid4()),
            "provider": "pagerduty",
            "external_id": f"inc-{uuid.uuid4()}",
            "title": "Service Outage",
            "severity": "P1",
            "started_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 404
