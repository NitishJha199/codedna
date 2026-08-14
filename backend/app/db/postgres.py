from collections.abc import Generator

import psycopg
from psycopg import Connection

from backend.app.core.config import settings


def get_connection() -> Connection:
    return psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )


def connection_dependency() -> Generator[Connection, None, None]:
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()
