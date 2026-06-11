import torch
import httpx
from fastapi import FastAPI, Depends
from pathlib import Path

from api.config import (
    OLLAMA_URL, TTS_URL, TTS_USER, TTS_PASS,
    UPLOAD_DIR, RESULT_DIR, MODEL_TTL,
)
from api.utils.model_manager import ModelManager
from api.utils.cleanup import AutoCleaner
from api.auth import verify
from api.routers import chat, tts, generate, talk

app = FastAPI(
    title="Osaka AI Hub",
    description="Unified AI API: LLM, TTS, Digital Human",
    dependencies=[Depends(verify)],
)

mm = ModelManager(evict_interval=60)

from api.engines import sadtalker
mm.register("sadtalker", sadtalker.loader, sadtalker.unloader, ttl=MODEL_TTL)

generate.init(mm)
talk.init(mm)

app.include_router(chat.router)
app.include_router(tts.router)
app.include_router(generate.router)
app.include_router(talk.router)

_cleaner = AutoCleaner([UPLOAD_DIR, RESULT_DIR, Path("/tmp")], interval=600, max_age=3600)


VOICES = [
    "af_heart", "af_alloy", "af_bella", "af_jessica", "af_nicole",
    "af_nova", "af_river", "af_sarah", "af_sky",
    "am_adam", "am_echo", "am_liam", "am_michael", "am_onyx",
]


@app.get("/health")
async def health():
    services = {}
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            models = [m["name"] for m in r.json().get("models", [])]
            services["llm"] = {"status": "ok", "models": models}
        except Exception:
            services["llm"] = {"status": "down"}
        try:
            await client.get(f"{TTS_URL}/", auth=(TTS_USER, TTS_PASS))
            services["tts"] = {"status": "ok"}
        except Exception:
            services["tts"] = {"status": "down"}

    services["models"] = mm.status()

    return {
        "status": "ok",
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "vram_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.0f}GB" if torch.cuda.is_available() else None,
        "services": services,
    }


@app.get("/api/services")
async def list_services():
    return {
        "endpoints": {
            "POST /api/chat": "LLM chat (Qwen3.6-27B via Ollama, vision-capable). Params: message, model, stream, image (optional file upload for VLM)",
            "POST /api/tts": "Text-to-Speech (Kokoro, 14 voices). Params: text, voice",
            "POST /api/generate": "Digital human video. Params: text|audio, image, voice, engine(sadtalker|musetalk)",
            "POST /api/talk": "Full pipeline: LLM→TTS→Digital Human. Params: message, model, voice, engine, image",
            "GET /health": "System health + service status + model loading state",
            "GET /api/services": "This endpoint",
        },
        "voices": VOICES,
        "engines": {
            "sadtalker": "On-demand loaded, ~10s per video, auto-unloads after idle",
            "musetalk": "Subprocess-based, ~35s per video, no persistent VRAM usage",
        },
        "llm_models": ["qwen3.6:27b"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18801)
