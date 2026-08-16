from fastapi import FastAPI

from backend.app.api.builds import router as builds_router
from backend.app.api.environments import router as environments_router
from backend.app.api.artifacts import router as artifacts_router
from backend.app.api.container_images import router as container_images_router
from backend.app.api.dependencies import router as dependencies_router
from backend.app.api.security_findings import router as security_findings_router
from backend.app.api.commits import router as commits_router
from backend.app.api.developers import router as developers_router
from backend.app.api.health import router as health_router
from backend.app.api.organizations import router as organizations_router
from backend.app.api.pull_requests import router as pull_requests_router
from backend.app.api.pipelines import router as pipelines_router
from backend.app.api.projects import router as projects_router
from backend.app.api.repositories import router as repositories_router

app = FastAPI(
    title="CodeDNA API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(builds_router)
app.include_router(environments_router)
app.include_router(artifacts_router)
app.include_router(container_images_router)
app.include_router(dependencies_router)
app.include_router(security_findings_router)
app.include_router(commits_router)
app.include_router(developers_router)
app.include_router(organizations_router)
app.include_router(pull_requests_router)
app.include_router(pipelines_router)
app.include_router(projects_router)
app.include_router(repositories_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
