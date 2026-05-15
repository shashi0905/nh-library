"""Application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Neighborhood Library", version="0.1.0")


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
