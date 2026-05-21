# Osaka AI Hub

Unified AI API running on osaka (RTX PRO 6000 Blackwell, 96GB VRAM).

## Services

| Endpoint | Description |
|----------|-------------|
| `POST /api/chat` | LLM chat (Qwen3.6-27B) |
| `POST /api/tts` | Text-to-Speech (Kokoro, 14 voices) |
| `POST /api/generate` | Digital human video (SadTalker / MuseTalk) |
| `POST /api/talk` | Full pipeline: LLM → TTS → Digital Human |
| `GET /health` | Health check |

## Key Design Decisions

- **On-demand model loading**: AI models load on first request and auto-unload after idle (default 10 min TTL). Zero VRAM usage when idle.
- **Auto-cleanup**: Temporary files (uploads, results) are automatically cleaned every 10 minutes.
- **Clean deployment**: All project files live under `~/liyao/osaka-ai-hub/`. No file pollution outside this directory.

## Deployment

```bash
cd ~/liyao/osaka-ai-hub
uv venv && source .venv/bin/activate
uv pip install -e .
# Install engine-specific deps (SadTalker, MuseTalk) separately
python -m api.main
```

## Public Access

`http://154.17.17.154:18801` (via frpc → dmit1)
