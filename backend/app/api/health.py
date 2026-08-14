from fastapi import APIRouter

from backend.app.db.postgres import get_connection

router = APIRouter()


@router.get("/db/health")
def database_health() -> dict[str, str]:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

    return {"status": "ok"}
