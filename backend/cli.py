from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Forge Studio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8400)
    parser.add_argument("--dev", action="store_true", help="Run with auto-reload")
    args = parser.parse_args()

    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if not frontend_dist.is_dir():
        print(
            "Warning: frontend/dist not found. Run 'cd frontend && npm run build' first.",
            file=sys.stderr,
        )
        print("Starting backend only...", file=sys.stderr)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if args.dev:
        cmd.append("--reload")

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
