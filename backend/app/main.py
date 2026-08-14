from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.api.organizations import router as organizations_router

app = FastAPI(
    title="CodeDNA API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(organizations_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
