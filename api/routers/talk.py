import uuid
import asyncio
import httpx
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse

from api.config import OLLAMA_URL, DEFAULT_AVATAR, UPLOAD_DIR
from api.routers.tts import tts_generate

router = APIRouter()
_model_manager = None


def init(model_manager):
    global _model_manager
    _model_manager = model_manager


@router.post("/api/talk")
async def talk(
    message: str = Form(...),
    model: str = Form("qwen3.6:27b"),
    voice: str = Form("af_heart"),
    engine: str = Form("sadtalker"),
    image: UploadFile = File(None),
):
    if engine not in ("sadtalker", "musetalk"):
        raise HTTPException(400, "engine must be 'sadtalker' or 'musetalk'")

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": model, "messages": [{"role": "user", "content": message}], "stream": False},
            )
            resp.raise_for_status()
            llm_text = resp.json()["message"]["content"]
        except httpx.ConnectError:
            raise HTTPException(503, "Ollama service unavailable")
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, f"Ollama error: {e.response.status_code}")

    audio_path = await tts_generate(llm_text, voice)

    if image is not None:
        img_path = str(UPLOAD_DIR / f"{uuid.uuid4().hex}.png")
        with open(img_path, "wb") as f:
            f.write(await image.read())
    else:
        img_path = str(DEFAULT_AVATAR)

    try:
        if engine == "sadtalker":
            from api.engines import sadtalker
            models = _model_manager.get("sadtalker")
            video_path = await asyncio.to_thread(sadtalker.generate, img_path, audio_path, models)
        else:
            from api.engines import musetalk
            video_path = await asyncio.to_thread(musetalk.generate, img_path, audio_path)
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")

    from urllib.parse import quote
    # percent-encode: header values must be ASCII with no leading/trailing whitespace (h11 enforces)
    safe_header = quote(llm_text[:200], safe="")
    return FileResponse(
        video_path, media_type="video/mp4", filename="talk.mp4",
        headers={"X-LLM-Response": safe_header},
    )
