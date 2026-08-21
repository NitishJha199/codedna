from backend.app.api.metrics import router as metrics_router
from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.api.organizations import router as organizations_router
from backend.app.api.projects import router as projects_router
from backend.app.api.repositories import router as repositories_router
from backend.app.api.pipelines import router as pipelines_router
from backend.app.api.builds import router as builds_router
from backend.app.api.artifacts import router as artifacts_router
from backend.app.api.container_images import router as container_images_router
from backend.app.api.dependencies import router as dependencies_router
from backend.app.api.security_findings import router as security_findings_router
from backend.app.api.services import router as services_router
from backend.app.api.sboms import router as sboms_router
from backend.app.api.vulnerabilities import router as vulnerabilities_router
from backend.app.api.events import router as events_router
from backend.app.api.deployments import router as deployments_router
from backend.app.api.commits import router as commits_router
from backend.app.api.developers import router as developers_router
from backend.app.api.environments import router as environments_router
from backend.app.api.pull_requests import router as pull_requests_router
from backend.app.api.lineage import router as lineage_router

app = FastAPI(
    title="CodeDNA API",
    version="0.1.0",
    description="Software engineering intelligence platform",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(health_router)
app.include_router(organizations_router)
app.include_router(projects_router)
app.include_router(repositories_router)
app.include_router(pipelines_router)
app.include_router(builds_router)
app.include_router(artifacts_router)
app.include_router(container_images_router)
app.include_router(dependencies_router)
app.include_router(security_findings_router)
app.include_router(services_router)
app.include_router(sboms_router)
app.include_router(vulnerabilities_router)
app.include_router(events_router)
app.include_router(deployments_router)
app.include_router(commits_router)
app.include_router(developers_router)
app.include_router(environments_router)
app.include_router(pull_requests_router)
app.include_router(lineage_router)

app.include_router(metrics_router)
