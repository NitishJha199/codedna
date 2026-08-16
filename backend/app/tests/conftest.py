import pytest

from backend.app.db.postgres import get_connection


@pytest.fixture(autouse=True)
def cleanup_pytest_data():
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM security_findings
                WHERE provider = 'pytest'
            """)

            cur.execute("""
                DELETE FROM dependencies
                WHERE provider = 'pytest'
            """)

            cur.execute("""
                DELETE FROM services
                WHERE provider = 'pytest'
            """)

            cur.execute("""
                DELETE FROM environments
                WHERE provider = 'pytest'
            """)

            cur.execute("""
                DELETE FROM container_images
                WHERE registry = 'pytest-registry'
            """)

            cur.execute("""
                DELETE FROM artifacts
                WHERE provider = 'pytest'
            """)

        conn.commit()
        yield

    finally:
        conn.close()
