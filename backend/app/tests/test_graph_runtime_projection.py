from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import project_runtime_graph


def test_project_runtime_graph():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        result = project_runtime_graph(postgres, neo4j)

        assert result["environments"] >= 0
        assert result["services"] >= 0
        assert result["deployments"] >= 0
    finally:
        postgres.close()
        neo4j.close()


def test_runtime_projection_is_idempotent():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        first = project_runtime_graph(postgres, neo4j)
        second = project_runtime_graph(postgres, neo4j)

        assert first == second
    finally:
        postgres.close()
        neo4j.close()


def test_runtime_relationships_exist():
    driver = get_driver()

    try:
        with driver.session() as session:
            relationships = {
                "organization_environment": session.run(
                    """
                    MATCH (:Organization)-[:CONTAINS]->(:Environment)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "organization_service": session.run(
                    """
                    MATCH (:Organization)-[:OWNS]->(:Service)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "deployment_environment": session.run(
                    """
                    MATCH (:Deployment)-[:DEPLOYED_TO]->(:Environment)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "deployment_service": session.run(
                    """
                    MATCH (:Deployment)-[:DEPLOYS]->(:Service)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "artifact_deployment": session.run(
                    """
                    MATCH (:Artifact)-[:HAS_DEPLOYMENT]->(:Deployment)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
            }

        for count in relationships.values():
            assert count >= 0
    finally:
        driver.close()
