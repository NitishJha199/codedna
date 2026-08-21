from datetime import datetime, timezone
from psycopg import Connection
from psycopg.rows import dict_row

from backend.app.events.normalizer import process_single_event
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import project_security_graph


def process_pending_events(connection: Connection, batch_size: int = 50, sync_graph: bool = True) -> dict[str, int]:
    processed_count = 0
    failed_count = 0

    with connection.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, provider, event_type, payload
            FROM events
            WHERE processing_status = 'pending'
            ORDER BY created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED
            """,
            (batch_size,),
        )
        events = cur.fetchall()

    for event in events:
        event_id = event["id"]
        try:
            process_single_event(connection, event)
            with connection.cursor() as cur:
                cur.execute(
                    """
                    UPDATE events
                    SET processing_status = 'processed',
                        processed_at = %s,
                        error_message = NULL
                    WHERE id = %s
                    """,
                    (datetime.now(timezone.utc), event_id),
                )
            connection.commit()
            processed_count += 1
        except Exception as exc:
            connection.rollback()
            with connection.cursor() as cur:
                cur.execute(
                    """
                    UPDATE events
                    SET processing_status = 'failed',
                        processed_at = %s,
                        error_message = %s
                    WHERE id = %s
                    """,
                    (datetime.now(timezone.utc), str(exc), event_id),
                )
            connection.commit()
            failed_count += 1

    if processed_count > 0 and sync_graph:
        neo4j_driver = get_driver()
        try:
            project_security_graph(connection, neo4j_driver)
        finally:
            neo4j_driver.close()

    return {"processed": processed_count, "failed": failed_count}
