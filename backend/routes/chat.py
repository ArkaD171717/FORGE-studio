from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.engine import get_engine

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    mode: str | None = None
    max_tokens: int = 8192


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    thinking_content: str | None = None


@router.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    engine = get_engine()
    mode = req.mode if req.mode in ("think", "no_think") else None
    response = await asyncio.to_thread(
        engine.chat,
        req.message,
        mode=mode,
        max_tokens=req.max_tokens,
    )
    msg = response.choices[0].message
    return ChatResponse(
        content=msg.content or "",
        thinking_content=getattr(msg, "reasoning_content", None),
    )


def _stream_chat(engine, message, mode, max_tokens):
    return list(
        engine.chat(
            message,
            mode=mode,
            max_tokens=max_tokens,
            stream=True,
        )
    )


@router.websocket("/api/chat/stream")
async def chat_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            message = data.get("message", "")
            mode = data.get("mode")
            max_tokens = data.get("max_tokens", 8192)

            if mode not in ("think", "no_think", None):
                mode = None

            engine = get_engine()
            try:
                chunks = await asyncio.to_thread(
                    _stream_chat,
                    engine,
                    message,
                    mode,
                    max_tokens,
                )

                thinking_buf = []
                content_buf = []

                for chunk in chunks:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta is None:
                        continue

                    reasoning = getattr(delta, "reasoning_content", None)
                    if reasoning:
                        thinking_buf.append(reasoning)
                        await ws.send_json(
                            {
                                "type": "thinking",
                                "content": reasoning,
                            }
                        )

                    if delta.content:
                        content_buf.append(delta.content)
                        await ws.send_json(
                            {
                                "type": "response",
                                "content": delta.content,
                            }
                        )

                await ws.send_json(
                    {
                        "type": "done",
                        "content": "",
                        "full_thinking": "".join(thinking_buf),
                        "full_response": "".join(content_buf),
                    }
                )

            except Exception as exc:
                await ws.send_json(
                    {
                        "type": "error",
                        "content": str(exc),
                    }
                )

    except WebSocketDisconnect:
        pass
