from datetime import datetime, timezone
from uuid import uuid4
from psycopg import Connection
from psycopg.rows import dict_row


def process_github_push_event(connection: Connection, payload: dict) -> None:
    repo_data = payload.get("repository", {})
    repo_name = repo_data.get("name") or repo_data.get("full_name") or "unknown-repo"
    repo_ext_id = str(repo_data.get("id") or repo_name)
    org_name = repo_data.get("owner", {}).get("login") or repo_data.get("owner", {}).get("name") or "default-org"
    org_ext_id = f"gh-org-{org_name}"

    sender = payload.get("sender", {})
    dev_username = sender.get("login") or "unknown-dev"
    dev_ext_id = str(sender.get("id") or dev_username)

    commits = list(payload.get("commits", []))
    head_commit = payload.get("head_commit")
    if head_commit and head_commit not in commits:
        commits.append(head_commit)

    with connection.cursor(row_factory=dict_row) as cur:
        # 1. Upsert Organization: UNIQUE (provider, external_id)
        cur.execute(
            """
            INSERT INTO organizations (id, name, provider, external_id)
            VALUES (%s, %s, 'github', %s)
            ON CONFLICT (provider, external_id) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (uuid4(), org_name, org_ext_id),
        )
        org_id = cur.fetchone()["id"]

        # 2. Upsert Project: UNIQUE (organization_id, provider, external_id)
        cur.execute(
            """
            INSERT INTO projects (id, organization_id, name, provider, external_id)
            VALUES (%s, %s, %s, 'github', %s)
            ON CONFLICT (organization_id, provider, external_id) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (uuid4(), org_id, f"{org_name}-project", f"gh-proj-{org_name}"),
        )
        project_id = cur.fetchone()["id"]

        # 3. Upsert Repository: UNIQUE (provider, external_id)
        cur.execute(
            """
            INSERT INTO repositories (id, project_id, name, provider, external_id)
            VALUES (%s, %s, %s, 'github', %s)
            ON CONFLICT (provider, external_id) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (uuid4(), project_id, repo_name, repo_ext_id),
        )
        repo_id = cur.fetchone()["id"]

        # 4. Upsert Developer: UNIQUE (provider, external_id)
        cur.execute(
            """
            INSERT INTO developers (id, organization_id, username, display_name, provider, external_id)
            VALUES (%s, %s, %s, %s, 'github', %s)
            ON CONFLICT (provider, external_id) DO UPDATE SET username = EXCLUDED.username
            RETURNING id
            """,
            (uuid4(), org_id, dev_username, dev_username, dev_ext_id),
        )
        dev_id = cur.fetchone()["id"]

        # 5. Upsert Commits: UNIQUE (provider, external_id)
        for commit in commits:
            commit_sha = commit.get("id") or commit.get("sha")
            if not commit_sha:
                continue
            message = commit.get("message", "")
            cur.execute(
                """
                INSERT INTO commits (id, repository_id, developer_id, provider, external_id, sha, message, occurred_at)
                VALUES (%s, %s, %s, 'github', %s, %s, %s, %s)
                ON CONFLICT (provider, external_id) DO UPDATE SET message = EXCLUDED.message
                """,
                (uuid4(), repo_id, dev_id, f"gh-commit-{commit_sha}", commit_sha, message, datetime.now(timezone.utc)),
            )


def process_single_event(connection: Connection, event_row: dict) -> None:
    provider = event_row["provider"]
    event_type = event_row["event_type"]
    payload = event_row["payload"]

    if provider == "github" and event_type in ("push", "workflow_run"):
        process_github_push_event(connection, payload)
