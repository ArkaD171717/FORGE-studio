from __future__ import annotations

import asyncio
import logging
import platform
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from backend.engine import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()

_BLOCKED_PREFIXES_POSIX = ("/etc", "/usr", "/bin", "/sbin")
_BLOCKED_PREFIXES_WIN = ("C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)")


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


class CommandResponse(BaseModel):
    ok: bool
    mode: str | None = None
    backend: str | None = None
    error: str | None = None


def _validate_local_path(raw: str) -> str | None:
    """Return an error message if *raw* is not a safe local directory, else None."""
    resolved = Path(raw).resolve()
    if not resolved.is_dir():
        return "Path does not exist or is not a directory"
    resolved_str = str(resolved)
    if platform.system() == "Windows":
        blocked = _BLOCKED_PREFIXES_WIN
    else:
        blocked = _BLOCKED_PREFIXES_POSIX
    for prefix in blocked:
        if resolved_str.startswith(prefix):
            return f"Ingesting system directories is not allowed: {prefix}"
    return None


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
    except Exception:
        logger.exception("Ingest failed for %s", req.repo_url)
        return IngestResponse(ok=False, error="Internal error during ingest")


@router.post("/api/ingest-local")
async def ingest_local(req: IngestLocalRequest) -> IngestResponse:
    err = _validate_local_path(req.path)
    if err is not None:
        return IngestResponse(ok=False, error=err)

    engine = get_engine()
    try:
        pack = await asyncio.to_thread(
            engine.ingest_local,
            req.path,
            max_tokens=req.max_tokens,
        )
        return IngestResponse(ok=True, tokens=len(pack))
    except Exception:
        logger.exception("Local ingest failed for %s", req.path)
        return IngestResponse(ok=False, error="Internal error during local ingest")


@router.get("/api/mtp")
async def mtp_recommendation() -> dict:
    engine = get_engine()
    rec = engine.mtp_recommendation
    if rec is None:
        return {"available": False}
    return {"available": True, **rec.to_dict()}


@router.post("/api/thinking-mode")
async def set_thinking_mode(req: ThinkingModeRequest) -> CommandResponse:
    engine = get_engine()
    if req.mode not in ("think", "no_think"):
        return CommandResponse(ok=False, error="mode must be 'think' or 'no_think'")
    engine.session.set_thinking_mode(req.mode)
    return CommandResponse(ok=True, mode=req.mode)


@router.post("/api/backend")
async def set_backend(req: BackendRequest) -> CommandResponse:
    engine = get_engine()
    try:
        engine.session.set_backend(req.backend)
        return CommandResponse(ok=True, backend=req.backend)
    except Exception:
        logger.exception("Backend switch failed for %s", req.backend)
        return CommandResponse(ok=False, error="Internal error setting backend")
