"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1 import auth, books, loans, members

router = APIRouter(prefix="/api/v1")

router.include_router(books.router)
router.include_router(members.router)
router.include_router(loans.router)
router.include_router(auth.router)
