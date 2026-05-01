from __future__ import annotations

from fastapi import APIRouter

from backend.engine import get_engine

router = APIRouter()


@router.get("/api/messages")
async def messages() -> list[dict]:
    engine = get_engine()
    return [
        {
            "role": m.role,
            "content": m.content,
            "thinking_content": m.thinking_content,
            "token_count": m.token_count,
        }
        for m in engine.session.messages
    ]
