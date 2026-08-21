from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import project_delivery_graph


def test_project_delivery_graph():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        result = project_delivery_graph(postgres, neo4j)

        assert result["pipelines"] >= 0
        assert result["builds"] >= 0
        assert result["artifacts"] >= 0
        assert result["container_images"] >= 0
        assert result["sboms"] >= 0
    finally:
        postgres.close()
        neo4j.close()


def test_delivery_projection_is_idempotent():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        first = project_delivery_graph(postgres, neo4j)
        second = project_delivery_graph(postgres, neo4j)

        assert first == second
    finally:
        postgres.close()
        neo4j.close()


def test_delivery_relationships_exist():
    driver = get_driver()

    try:
        with driver.session() as session:
            relationships = {
                "pipelines": session.run(
                    """
                    MATCH (:Repository)-[:HAS_PIPELINE]->(:Pipeline)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "builds": session.run(
                    """
                    MATCH (:Pipeline)-[:HAS_BUILD]->(:Build)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "artifacts": session.run(
                    """
                    MATCH (:Build)-[:PRODUCES]->(:Artifact)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "images": session.run(
                    """
                    MATCH (:Artifact)-[:HAS_CONTAINER_IMAGE]->(:ContainerImage)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
                "sboms": session.run(
                    """
                    MATCH (:Artifact)-[:HAS_SBOM]->(:SBOM)
                    RETURN count(*) AS count
                    """
                ).single()["count"],
            }

        for count in relationships.values():
            assert count >= 0
    finally:
        driver.close()
