from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID
from psycopg import Connection
from psycopg.rows import dict_row


def get_dora_metrics(
    connection: Connection,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    environment_id: UUID | None = None,
    service_id: UUID | None = None,
) -> dict[str, Any]:
    if not end_time:
        end_time = datetime.now(timezone.utc)
    if not start_time:
        start_time = end_time - timedelta(days=30)

    params: list[Any] = [start_time, end_time]
    filters = ["deployed_at >= %s", "deployed_at <= %s"]

    if environment_id:
        filters.append("environment_id = %s")
        params.append(environment_id)
    if service_id:
        filters.append("service_id = %s")
        params.append(service_id)

    where_clause = " AND ".join(filters)

    with connection.cursor(row_factory=dict_row) as cursor:
        # 1. Total and Successful Deployments
        cursor.execute(
            f"""
            SELECT
                count(*) AS total_deployments,
                count(*) FILTER (WHERE lower(status) IN ('success', 'successful', 'passed')) AS successful_deployments,
                count(*) FILTER (WHERE lower(status) IN ('failed', 'failure', 'error')) AS failed_deployments
            FROM deployments
            WHERE {where_clause}
            """,
            params,
        )
        dep_summary = cursor.fetchone() or {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
        }

        total = dep_summary["total_deployments"]
        successful = dep_summary["successful_deployments"]
        failed = dep_summary["failed_deployments"]

        # 2. Change Failure Rate
        change_failure_rate = (failed / total * 100.0) if total > 0 else 0.0

        # 3. Deployment Frequency
        days = max((end_time - start_time).total_seconds() / 86400.0, 1.0)
        deployment_frequency_per_day = round(successful / days, 3)

        # 4. Lead Time for Changes (Commit to Deployment)
        lead_time_query = f"""
            SELECT
                AVG(EXTRACT(EPOCH FROM (d.deployed_at - c.occurred_at))) AS avg_lead_time_seconds
            FROM deployments d
            JOIN artifacts a ON d.artifact_id = a.id
            JOIN builds b ON a.build_id = b.id
            JOIN commits c ON b.commit_id = c.id
            WHERE {where_clause.replace('deployed_at', 'd.deployed_at').replace('environment_id', 'd.environment_id').replace('service_id', 'd.service_id')}
              AND d.deployed_at IS NOT NULL
              AND c.occurred_at IS NOT NULL
              AND d.deployed_at >= c.occurred_at
        """
        cursor.execute(lead_time_query, params)
        lead_row = cursor.fetchone()
        avg_lead_time_seconds = (
            float(lead_row["avg_lead_time_seconds"])
            if lead_row and lead_row["avg_lead_time_seconds"] is not None
            else None
        )

        # 5. Mean Time to Restore (MTTR) from Incidents
        incident_params: list[Any] = [start_time, end_time]
        inc_filters = ["started_at >= %s", "started_at <= %s"]
        if environment_id:
            inc_filters.append("environment_id = %s")
            incident_params.append(environment_id)
        if service_id:
            inc_filters.append("service_id = %s")
            incident_params.append(service_id)

        inc_where = " AND ".join(inc_filters)

        cursor.execute(
            f"""
            SELECT
                count(*) AS total_incidents,
                count(*) FILTER (WHERE resolved_at IS NOT NULL) AS resolved_incidents,
                AVG(EXTRACT(EPOCH FROM (resolved_at - started_at))) AS avg_recovery_seconds
            FROM incidents
            WHERE {inc_where}
            """,
            incident_params,
        )
        inc_row = cursor.fetchone() or {
            "total_incidents": 0,
            "resolved_incidents": 0,
            "avg_recovery_seconds": None,
        }

        avg_mttr_seconds = (
            float(inc_row["avg_recovery_seconds"])
            if inc_row["avg_recovery_seconds"] is not None
            else None
        )

        return {
            "time_window": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_days": round(days, 2),
            },
            "deployments": {
                "total": total,
                "successful": successful,
                "failed": failed,
            },
            "deployment_frequency": {
                "deployments_per_day": deployment_frequency_per_day,
                "total_successful": successful,
            },
            "change_failure_rate": {
                "rate_percentage": round(change_failure_rate, 2),
                "failed_count": failed,
                "total_count": total,
            },
            "lead_time_for_changes": {
                "avg_lead_time_seconds": avg_lead_time_seconds,
                "avg_lead_time_hours": (
                    round(avg_lead_time_seconds / 3600.0, 2)
                    if avg_lead_time_seconds is not None
                    else None
                ),
            },
            "mean_time_to_restore": {
                "total_incidents": inc_row["total_incidents"],
                "resolved_incidents": inc_row["resolved_incidents"],
                "avg_recovery_seconds": avg_mttr_seconds,
                "avg_recovery_minutes": (
                    round(avg_mttr_seconds / 60.0, 2)
                    if avg_mttr_seconds is not None
                    else None
                ),
            },
        }
