"""Application entry point."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.exceptions import LibraryException

app = FastAPI(title="Neighborhood Library", version="0.1.0")

# Include API routers
app.include_router(v1_router)


# Exception handlers
@app.exception_handler(LibraryException)
async def library_exception_handler(request: Request, exc: LibraryException) -> JSONResponse:
    """Handle library domain exceptions with RFC 7807 compliance."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://example.com/errors/{exc.__class__.__name__.lower()}",
            "title": exc.__class__.__name__,
            "status": exc.status_code,
            "detail": exc.message,
            "instance": str(request.url),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}
