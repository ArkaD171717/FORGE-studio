from __future__ import annotations

import asyncio

from fastapi import APIRouter
from pydantic import BaseModel

from backend.engine import get_engine

router = APIRouter()


class IngestRequest(BaseModel):
    repo_url: str
    branch: str | None = None
    max_tokens: int | None = None


class IngestLocalRequest(BaseModel):
    path: str
    max_tokens: int | None = None


class IngestResponse(BaseModel):
    ok: bool
    tokens: int = 0
    error: str | None = None


class ThinkingModeRequest(BaseModel):
    mode: str


class BackendRequest(BaseModel):
    backend: str


@router.post("/api/ingest")
async def ingest(req: IngestRequest) -> IngestResponse:
    engine = get_engine()
    try:
        pack = await asyncio.to_thread(
            engine.ingest,
            req.repo_url,
            branch=req.branch,
            max_tokens=req.max_tokens,
        )
        return IngestResponse(ok=True, tokens=len(pack))
    except Exception as e:
        return IngestResponse(ok=False, error=str(e))


@router.post("/api/ingest-local")
async def ingest_local(req: IngestLocalRequest) -> IngestResponse:
    engine = get_engine()
    try:
        pack = await asyncio.to_thread(
            engine.ingest_local,
            req.path,
            max_tokens=req.max_tokens,
        )
        return IngestResponse(ok=True, tokens=len(pack))
    except Exception as e:
        return IngestResponse(ok=False, error=str(e))


@router.get("/api/mtp")
async def mtp_recommendation() -> dict:
    engine = get_engine()
    rec = engine.mtp_recommendation
    if rec is None:
        return {"available": False}
    return {"available": True, **rec.to_dict()}


@router.post("/api/thinking-mode")
async def set_thinking_mode(req: ThinkingModeRequest) -> dict:
    engine = get_engine()
    if req.mode not in ("think", "no_think"):
        return {"ok": False, "error": "mode must be 'think' or 'no_think'"}
    engine.session.set_thinking_mode(req.mode)
    return {"ok": True, "mode": req.mode}


@router.post("/api/backend")
async def set_backend(req: BackendRequest) -> dict:
    engine = get_engine()
    try:
        engine.session.set_backend(req.backend)
        return {"ok": True, "backend": req.backend}
    except Exception as e:
        return {"ok": False, "error": str(e)}
