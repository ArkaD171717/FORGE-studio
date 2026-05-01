# forge-studio

Web UI for ForgeEngine. FastAPI backend with a React frontend -- chat with Qwen3.6 reasoning models, ingest repos, toggle thinking mode, view token budget.

## Install

```bash
pip install -e ".[dev]"
cd frontend && npm install && npm run build && cd ..
```

## Run

```bash
# Set your inference backend
export FORGE_MODEL=Qwen3.6-27B
export FORGE_BASE_URL=http://localhost:8000/v1

# Start the server (binds to 127.0.0.1 by default)
forge-studio --port 8400
```

Open http://localhost:8400 in your browser.

### Development mode

Run backend and frontend separately for hot reloading:

```bash
# Terminal 1: backend with auto-reload
forge-studio --port 8400 --dev

# Terminal 2: frontend dev server (proxies API to backend)
cd frontend && npm run dev
```

The Vite dev server runs on port 5173 and proxies `/api` requests to the backend on port 8400.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| FORGE_MODEL | Qwen3.6-27B | Model name |
| FORGE_BASE_URL | http://localhost:8000/v1 | Inference API endpoint |
| FORGE_API_KEY | EMPTY | API key for the endpoint |
| FORGE_BACKEND | (auto) | Backend type: vllm, sglang, dashscope |
| FORGE_GPU_ID | (none) | GPU ID for MTP recommendation |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/chat | Non-streaming chat |
| WS | /api/chat/stream | Streaming chat via WebSocket |
| GET | /api/status | Engine status and budget info |
| GET | /api/messages | Conversation history |
| POST | /api/ingest | Ingest a git repository |
| POST | /api/ingest-local | Ingest a local repo path |
| GET | /api/mtp | MTP recommendation |
| POST | /api/thinking-mode | Set thinking mode (think/no_think) |
| POST | /api/backend | Switch backend type |

## Tests

```bash
pytest -x -q
```

## License

Apache 2.0
