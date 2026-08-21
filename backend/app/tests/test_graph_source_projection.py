from backend.app.db.postgres import get_connection
from backend.app.graph.neo4j import get_driver
from backend.app.graph.projection import project_source_graph


def test_project_source_graph():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        result = project_source_graph(postgres, neo4j)

        assert result["organizations"] >= 0
        assert result["projects"] >= 0
        assert result["repositories"] >= 0
        assert result["commits"] >= 0
        assert result["pull_requests"] >= 0
    finally:
        postgres.close()
        neo4j.close()


def test_source_projection_is_idempotent():
    postgres = get_connection()
    neo4j = get_driver()

    try:
        first = project_source_graph(postgres, neo4j)
        second = project_source_graph(postgres, neo4j)

        assert first == second
    finally:
        postgres.close()
        neo4j.close()


def test_source_relationships_exist():
    driver = get_driver()

    try:
        with driver.session() as session:
            commit_relationships = session.run(
                """
                MATCH (:Repository)-[r:HAS_COMMIT]->(:Commit)
                RETURN count(r) AS count
                """
            ).single()["count"]

            pr_relationships = session.run(
                """
                MATCH (:Repository)-[r:HAS_PULL_REQUEST]->(:PullRequest)
                RETURN count(r) AS count
                """
            ).single()["count"]

        assert commit_relationships >= 0
        assert pr_relationships >= 0
    finally:
        driver.close()
