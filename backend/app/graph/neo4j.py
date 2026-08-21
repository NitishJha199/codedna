from collections.abc import Generator

from neo4j import Driver, GraphDatabase

from backend.app.core.config import settings


def get_driver() -> Driver:
    return GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


def verify_connection(driver: Driver | None = None) -> bool:
    owned_driver = driver is None
    active_driver = driver or get_driver()

    try:
        active_driver.verify_connectivity()
        return True
    finally:
        if owned_driver:
            active_driver.close()


def driver_dependency() -> Generator[Driver, None, None]:
    driver = get_driver()
    try:
        yield driver
    finally:
        driver.close()
