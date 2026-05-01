"""Standalone mock server for UI testing. No forge dependency required.

Usage:
    python -m backend.mock_server
    python -m backend.mock_server --port 8400
"""

from __future__ import annotations

import argparse
import asyncio
import random
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Forge Studio (mock)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_state = {
    "model": "Qwen3.6-27B",
    "backend": "vllm",
    "thinking_mode": "think",
    "used_tokens": 48200,
    "total_tokens": 200000,
    "messages": 0,
    "context_tokens": 0,
    "context_files": 0,
}

MOCK_RESPONSES = [
    (
        "The Qwen3.6 model uses a Mixture-of-Experts architecture with"
        " 235B total parameters, of which roughly 22B are active per token."
    ),
    (
        "To enable MTP with vLLM, pass `--num-speculative-tokens 3` and"
        " ensure the draft model weights are available. Expected gain: 15-25%."
    ),
    (
        "The token budget tracks cumulative usage across the session."
        " At 80% it suggests compressing older context. At 95% it refuses."
    ),
    (
        "The main issue is that the async handler calls a blocking function"
        " on the event loop. Wrapping with `asyncio.to_thread()` fixes it."
    ),
]

MOCK_THINKING = [
    (
        "Let me analyze the architecture. The user is asking about inference"
        " backends -- vLLM, SGLang, and DashScope each have different"
        " trade-offs for latency vs throughput..."
    ),
    (
        "The session has used about 24% of the budget so far. The remaining"
        " 150K tokens should be enough, but I should keep responses concise..."
    ),
    (
        "Let me trace the execution path: request comes in through FastAPI,"
        " hits the router, calls get_engine(), returns the singleton,"
        " then delegates to the OpenAI client..."
    ),
]


class ChatRequest(BaseModel):
    message: str
    mode: str | None = None
    max_tokens: int = 8192


class IngestRequest(BaseModel):
    repo_url: str
    branch: str | None = None
    max_tokens: int | None = None


class IngestLocalRequest(BaseModel):
    path: str
    max_tokens: int | None = None


class ModeRequest(BaseModel):
    mode: str


class BackendRequest(BaseModel):
    backend: str


@app.get("/api/status")
async def status():
    return {
        "model": _state["model"],
        "model_hf": f"Qwen/{_state['model']}",
        "backend": _state["backend"],
        "base_url": "http://localhost:8000/v1",
        "thinking_mode": _state["thinking_mode"],
        "budget": {
            "total": _state["total_tokens"],
            "used": _state["used_tokens"],
            "available": _state["total_tokens"] - _state["used_tokens"],
            "action": "ok" if _state["used_tokens"] < 160000 else "warn",
        },
        "messages": _state["messages"],
        "context": {
            "tokens": _state["context_tokens"],
            "files": _state["context_files"],
        }
        if _state["context_tokens"] > 0
        else None,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    _state["messages"] += 2
    _state["used_tokens"] += random.randint(800, 2400)
    content = random.choice(MOCK_RESPONSES)
    thinking = random.choice(MOCK_THINKING) if _state["thinking_mode"] == "think" else None
    return {
        "role": "assistant",
        "content": content,
        "thinking_content": thinking,
    }


@app.websocket("/api/chat/stream")
async def chat_stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            mode = data.get("mode")

            _state["messages"] += 2
            _state["used_tokens"] += random.randint(800, 2400)

            use_thinking = mode == "think" or (mode is None and _state["thinking_mode"] == "think")

            if use_thinking:
                thinking_text = random.choice(MOCK_THINKING)
                for i in range(0, len(thinking_text), 8):
                    chunk = thinking_text[i : i + 8]
                    await ws.send_json({"type": "thinking", "content": chunk})
                    await asyncio.sleep(0.03)

            response_text = random.choice(MOCK_RESPONSES)
            for i in range(0, len(response_text), 6):
                chunk = response_text[i : i + 6]
                await ws.send_json({"type": "response", "content": chunk})
                await asyncio.sleep(0.025)

            await ws.send_json(
                {
                    "type": "done",
                    "content": "",
                    "full_thinking": thinking_text if use_thinking else "",
                    "full_response": response_text,
                }
            )

    except WebSocketDisconnect:
        pass


@app.get("/api/messages")
async def messages():
    return []


@app.get("/api/mtp")
async def mtp():
    return {
        "available": True,
        "enable": True,
        "reason": "GPU has sufficient VRAM for speculative decoding",
        "num_speculative_tokens": 3,
        "expected_gain": "15-25%",
        "warnings": [],
        "vllm_command": "vllm serve Qwen/Qwen3.6-27B --num-speculative-tokens 3",
        "sglang_command": None,
    }


@app.post("/api/ingest")
async def ingest(req: IngestRequest):
    await asyncio.sleep(1.5)
    tokens = random.randint(12000, 45000)
    _state["context_tokens"] = tokens
    _state["context_files"] = random.randint(15, 80)
    _state["used_tokens"] += tokens
    return {"ok": True, "tokens": tokens}


@app.post("/api/ingest-local")
async def ingest_local(req: IngestLocalRequest):
    await asyncio.sleep(0.8)
    tokens = random.randint(8000, 30000)
    _state["context_tokens"] = tokens
    _state["context_files"] = random.randint(10, 50)
    _state["used_tokens"] += tokens
    return {"ok": True, "tokens": tokens}


@app.post("/api/thinking-mode")
async def set_thinking_mode(req: ModeRequest):
    if req.mode not in ("think", "no_think"):
        return {"ok": False, "error": "mode must be 'think' or 'no_think'"}
    _state["thinking_mode"] = req.mode
    return {"ok": True, "mode": req.mode}


@app.post("/api/backend")
async def set_backend(req: BackendRequest):
    if req.backend not in ("vllm", "sglang", "dashscope"):
        return {"ok": False, "error": f"unknown backend: {req.backend}"}
    _state["backend"] = req.backend
    return {"ok": True, "backend": req.backend}


static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(static_dir), html=True),
        name="static",
    )


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Forge Studio mock server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8400)
    args = parser.parse_args()
    print(f"Mock server at http://{args.host}:{args.port}")
    print("This serves fake data for UI testing -- no ForgeEngine needed.")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
