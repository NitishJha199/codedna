import uuid
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver

client = TestClient(app)


def compute_github_signature(payload_bytes: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def test_webhook_to_normalization_and_graph_sync():
    run_id = str(uuid.uuid4())[:8]
    delivery_id = str(uuid.uuid4())
    repo_name = f"repo-norm-{run_id}"
    dev_username = f"dev-{run_id}"
    sha = f"sha-{run_id}"

    payload = {
        "repository": {
            "id": f"gh-repo-id-{run_id}",
            "name": repo_name,
            "owner": {"login": f"org-{run_id}"},
        },
        "sender": {
            "id": f"gh-dev-id-{run_id}",
            "login": dev_username,
        },
        "commits": [
            {"id": sha, "message": "normalized commit message"}
        ],
    }

    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_github_signature(payload_bytes, settings.github_webhook_secret)

    # 1. Ingest webhook
    res = client.post(
        "/webhooks/github",
        headers={
            "X-GitHub-Event": "push",
            "X-GitHub-Delivery": delivery_id,
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json",
        },
        content=payload_bytes,
    )
    assert res.status_code == 202

    # 2. Trigger worker processing
    proc_res = client.post("/events/process-pending")
    assert proc_res.status_code == 200
    assert proc_res.json()["processed"] >= 1

    # 3. Verify PostgreSQL has normalized the entities
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM repositories WHERE name = %s", (repo_name,))
            repo = cur.fetchone()
            assert repo is not None

            cur.execute("SELECT * FROM commits WHERE sha = %s", (sha,))
            commit = cur.fetchone()
            assert commit is not None

    # 4. Verify Neo4j received the projected node
    driver = get_driver()
    with driver.session() as session:
        result = session.run("MATCH (r:Repository) WHERE r.name = $name RETURN r.name AS name", name=repo_name)
        record = result.single()
        assert record is not None
        assert record["name"] == repo_name
    driver.close()
