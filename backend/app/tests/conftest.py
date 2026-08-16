import pytest

from backend.app.db.postgres import get_connection


def cleanup_pytest_data():
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM deployments
                WHERE provider = 'pytest'
            """)

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
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    cleanup_pytest_data()

    yield

    cleanup_pytest_data()
