from __future__ import annotations

import os
from typing import Optional

from forge import ForgeEngine

_engine: Optional[ForgeEngine] = None


def get_engine() -> ForgeEngine:
    global _engine
    if _engine is None:
        _engine = ForgeEngine(
            model=os.environ.get("FORGE_MODEL", "Qwen3.6-27B"),
            base_url=os.environ.get("FORGE_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.environ.get("FORGE_API_KEY", "EMPTY"),
            backend=os.environ.get("FORGE_BACKEND"),
            gpu_id=os.environ.get("FORGE_GPU_ID"),
        )
    return _engine
