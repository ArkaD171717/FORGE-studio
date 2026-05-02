from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from typing import Any, Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@dataclass
class FakeMessage:
    role: str = "assistant"
    content: str = ""
    thinking_content: Optional[str] = None
    token_count: int = 0


@dataclass
class FakeBudgetStatus:
    total_tokens: int = 200000
    used_tokens: int = 50000
    available_tokens: int = 150000
    action: str = "ok"
    message: str = ""


@dataclass
class FakeSession:
    _messages: list = field(default_factory=list)
    _thinking_mode: str = "think"
    _budget: FakeBudgetStatus = field(default_factory=FakeBudgetStatus)
    _backend: str = "vllm"

    @property
    def messages(self) -> list:
        return list(self._messages)

    @property
    def thinking_mode(self) -> str:
        return self._thinking_mode

    @property
    def budget_status(self) -> FakeBudgetStatus:
        return self._budget

    def set_thinking_mode(self, mode: str) -> None:
        self._thinking_mode = mode

    def set_backend(self, backend: str) -> None:
        if backend not in ("vllm", "sglang", "dashscope"):
            raise ValueError(f"unknown backend: {backend}")
        self._backend = backend


@dataclass
class FakeMtpRec:
    enable: bool = True
    reason: str = "recommended"
    num_speculative_tokens: int = 3
    expected_gain: str = "15-25%"
    warnings: list = field(default_factory=list)
    vllm_command: Optional[str] = "vllm serve --num-speculative-tokens 3"
    sglang_command: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "enable": self.enable,
            "reason": self.reason,
            "num_speculative_tokens": self.num_speculative_tokens,
            "expected_gain": self.expected_gain,
            "warnings": self.warnings,
            "vllm_command": self.vllm_command,
            "sglang_command": self.sglang_command,
        }


@dataclass
class FakeChoice:
    message: FakeMessage = field(default_factory=FakeMessage)


@dataclass
class FakeResponse:
    choices: list = field(default_factory=lambda: [FakeChoice(FakeMessage(content="Hello!"))])


class FakeEngine:
    def __init__(self) -> None:
        self.model = "Qwen3.6-27B"
        self._session = FakeSession()
        self._mtp = FakeMtpRec()
        self._context_pack: Optional[str] = None
        self.chat_calls: list[dict] = []
        self.ingest_calls: list[str] = []

    @property
    def session(self) -> FakeSession:
        return self._session

    @property
    def mtp_recommendation(self) -> Optional[FakeMtpRec]:
        return self._mtp

    def chat(self, message: str, **kwargs: Any) -> FakeResponse:
        self.chat_calls.append({"message": message, **kwargs})
        return FakeResponse()

    def ingest(self, repo_url: str, **kwargs: Any) -> str:
        self.ingest_calls.append(repo_url)
        pack = f"[context for {repo_url}]"
        self._context_pack = pack
        return pack

    def ingest_local(self, path: str, **kwargs: Any) -> str:
        self.ingest_calls.append(path)
        pack = f"[context for {path}]"
        self._context_pack = pack
        return pack

    def status(self) -> dict:
        bs = self._session.budget_status
        result: dict[str, Any] = {
            "model": self.model,
            "model_hf": f"Qwen/{self.model}",
            "backend": self._session._backend,
            "base_url": "http://localhost:8000/v1",
            "thinking_mode": self._session.thinking_mode,
            "budget": {
                "total": bs.total_tokens,
                "used": bs.used_tokens,
                "available": bs.available_tokens,
                "action": bs.action,
            },
            "messages": len(self._session.messages),
        }
        return result


_fake_engine = FakeEngine()


def _get_fake_engine() -> FakeEngine:
    return _fake_engine


@pytest.fixture(autouse=True)
def _patch_engine():
    global _fake_engine
    _fake_engine = FakeEngine()
    with (
        patch("backend.routes.chat.get_engine", _get_fake_engine),
        patch("backend.routes.commands.get_engine", _get_fake_engine),
        patch("backend.routes.status.get_engine", _get_fake_engine),
        patch("backend.routes.history.get_engine", _get_fake_engine),
        patch("backend.main.get_engine", _get_fake_engine),
    ):
        yield


@pytest.fixture
def client():
    from backend.main import app

    return TestClient(app)


def test_status_returns_budget_and_model(client: TestClient) -> None:
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "Qwen3.6-27B"
    assert data["budget"]["total"] == 200000
    assert data["budget"]["used"] == 50000
    assert data["budget"]["available"] == 150000
    assert data["budget"]["action"] == "ok"
    assert data["thinking_mode"] == "think"
    assert data["backend"] == "vllm"
    assert data["messages"] == 0


def test_chat_returns_response_content(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "Hello!"
    assert data["thinking_content"] is None
    assert _fake_engine.chat_calls[0]["message"] == "hi"


def test_chat_forwards_mode(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "hi", "mode": "no_think"})
    assert resp.status_code == 200
    assert _fake_engine.chat_calls[0]["mode"] == "no_think"


def test_chat_drops_invalid_mode_to_none(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "hi", "mode": "bogus"})
    assert resp.status_code == 200
    assert _fake_engine.chat_calls[0]["mode"] is None


def test_messages_empty(client: TestClient) -> None:
    resp = client.get("/api/messages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_thinking_mode_toggles(client: TestClient) -> None:
    resp = client.post("/api/thinking-mode", json={"mode": "no_think"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.json()["mode"] == "no_think"

    status = client.get("/api/status").json()
    assert status["thinking_mode"] == "no_think"


def test_thinking_mode_rejects_invalid(client: TestClient) -> None:
    resp = client.post("/api/thinking-mode", json={"mode": "bad"})
    data = resp.json()
    assert data["ok"] is False
    assert "error" in data


def test_mtp_returns_recommendation(client: TestClient) -> None:
    resp = client.get("/api/mtp")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert data["enable"] is True
    assert data["num_speculative_tokens"] == 3
    assert data["expected_gain"] == "15-25%"


def test_ingest_calls_engine_and_returns_length(client: TestClient) -> None:
    url = "https://github.com/test/repo"
    resp = client.post("/api/ingest", json={"repo_url": url})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["tokens"] == len(f"[context for {url}]")
    assert _fake_engine.ingest_calls == [url]


def test_ingest_local_calls_engine(client: TestClient) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        resp = client.post("/api/ingest-local", json={"path": tmpdir})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["tokens"] == len(f"[context for {tmpdir}]")
        assert _fake_engine.ingest_calls == [tmpdir]


def test_ingest_local_rejects_nonexistent_path(client: TestClient) -> None:
    resp = client.post("/api/ingest-local", json={"path": "/no/such/path/exists"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert "not a directory" in data["error"].lower() or "does not exist" in data["error"].lower()


def test_backend_change_updates_session(client: TestClient) -> None:
    resp = client.post("/api/backend", json={"backend": "sglang"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert _fake_engine.session._backend == "sglang"


def test_backend_change_rejects_unknown(client: TestClient) -> None:
    resp = client.post("/api/backend", json={"backend": "unknown_backend"})
    data = resp.json()
    assert data["ok"] is False
    assert "error" in data
