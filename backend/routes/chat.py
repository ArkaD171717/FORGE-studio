from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterator
from queue import Empty, SimpleQueue

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.engine import get_engine

logger = logging.getLogger(__name__)

router = APIRouter()

_SENTINEL = object()


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


def _produce_chunks(iterator: Iterator, queue: SimpleQueue) -> None:
    """Drain *iterator* into *queue*, posting _SENTINEL when done."""
    try:
        for chunk in iterator:
            queue.put(chunk)
    except Exception as exc:
        queue.put(exc)
    finally:
        queue.put(_SENTINEL)


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
                stream_iter = engine.chat(
                    message,
                    mode=mode,
                    max_tokens=max_tokens,
                    stream=True,
                )

                queue: SimpleQueue = SimpleQueue()
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, _produce_chunks, stream_iter, queue)

                thinking_buf: list[str] = []
                content_buf: list[str] = []

                while True:
                    try:
                        item = queue.get_nowait()
                    except Empty:
                        await asyncio.sleep(0.01)
                        continue

                    if item is _SENTINEL:
                        break
                    if isinstance(item, Exception):
                        raise item

                    chunk = item
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

            except Exception:
                logger.exception("Error during streaming chat")
                await ws.send_json(
                    {
                        "type": "error",
                        "content": "Internal error during chat",
                    }
                )

    except WebSocketDisconnect:
        pass
