from fastapi import FastAPI

from backend.app.api.health import router as health_router

app = FastAPI(
    title="CodeDNA API",
    version="0.1.0",
)

app.include_router(health_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
