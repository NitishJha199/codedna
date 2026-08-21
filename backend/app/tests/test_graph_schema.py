from backend.app.graph.neo4j import get_driver, verify_connection
from backend.app.graph.schema import GRAPH_CONSTRAINTS, ensure_constraints


def test_neo4j_connection():
    assert verify_connection()


def test_graph_constraints_are_defined():
    assert len(GRAPH_CONSTRAINTS) == 17
    assert "repository_id" in GRAPH_CONSTRAINTS
    assert "security_finding_id" in GRAPH_CONSTRAINTS
    assert "deployment_id" in GRAPH_CONSTRAINTS


def test_ensure_constraints():
    driver = get_driver()

    try:
        ensure_constraints(driver)
        ensure_constraints(driver)
    finally:
        driver.close()
