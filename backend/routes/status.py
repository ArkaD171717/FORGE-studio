from __future__ import annotations

from fastapi import APIRouter

from backend.engine import get_engine

router = APIRouter()


@router.get("/api/status")
async def status() -> dict:
    engine = get_engine()
    return engine.status()
