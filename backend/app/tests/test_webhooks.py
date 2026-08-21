import hmac
import hashlib
import json
import uuid
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def compute_github_signature(payload_bytes: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_github_webhook_missing_headers():
    response = client.post("/webhooks/github", json={"ref": "refs/heads/main"})
    assert response.status_code == 400


def test_github_webhook_invalid_signature():
    delivery_id = str(uuid.uuid4())
    payload = {"action": "push", "ref": "refs/heads/main"}
    response = client.post(
        "/webhooks/github",
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": "sha256=invalid-signature-hex",
        },
        json=payload,
    )
    assert response.status_code == 401


def test_github_webhook_success_and_idempotency():
    delivery_id = str(uuid.uuid4())
    payload = {
        "action": "push",
        "repository": {"full_name": "org/repo"},
        "head_commit": {"id": "sha-123", "message": "test webhook commit"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_github_signature(payload_bytes, settings.github_webhook_secret)

    # 1. First delivery -> 202 Accepted
    response = client.post(
        "/webhooks/github",
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
        content=payload_bytes,
    )
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["idempotency_key"] == f"github:{delivery_id}"

    # 2. Duplicate delivery with same delivery_id -> Handled gracefully
    dup_response = client.post(
        "/webhooks/github",
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
        content=payload_bytes,
    )
    assert dup_response.status_code == 202
    dup_data = dup_response.json()
    assert dup_data["status"] == "duplicate"


def test_gitlab_webhook_success_and_invalid_token():
    # 1. Invalid Token -> 401
    bad_res = client.post(
        "/webhooks/gitlab",
        headers={
            "X-Gitlab-Event": "Push Hook",
            "X-Gitlab-Token": "wrong-token",
        },
        json={"event_name": "push"},
    )
    assert bad_res.status_code == 401

    # 2. Valid Token -> 202 Accepted
    event_uuid = str(uuid.uuid4())
    good_res = client.post(
        "/webhooks/gitlab",
        headers={
            "X-Gitlab-Event": "Push Hook",
            "X-Gitlab-Token": settings.gitlab_webhook_secret,
            "X-Gitlab-Event-UUID": event_uuid,
        },
        json={"event_name": "push", "project": {"name": "gitlab-project"}},
    )
    assert good_res.status_code == 202
    assert good_res.json()["status"] == "accepted"
