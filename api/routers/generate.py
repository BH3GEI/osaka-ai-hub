import uuid
import asyncio
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse

from api.config import DEFAULT_AVATAR, UPLOAD_DIR
from api.routers.tts import tts_generate

router = APIRouter()
_model_manager = None


def init(model_manager):
    global _model_manager
    _model_manager = model_manager


@router.post("/api/generate")
async def generate(
    text: str = Form(None),
    audio: UploadFile = File(None),
    image: UploadFile = File(None),
    voice: str = Form("af_heart"),
    engine: str = Form("sadtalker"),
):
    if text is None and audio is None:
        raise HTTPException(400, "Provide either 'text' or 'audio'")
    if engine not in ("sadtalker", "musetalk"):
        raise HTTPException(400, "engine must be 'sadtalker' or 'musetalk'")

    if image is not None:
        img_path = str(UPLOAD_DIR / f"{uuid.uuid4().hex}.png")
        with open(img_path, "wb") as f:
            f.write(await image.read())
    else:
        img_path = str(DEFAULT_AVATAR)

    if audio is not None:
        audio_path = str(UPLOAD_DIR / f"{uuid.uuid4().hex}.wav")
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
    else:
        audio_path = await tts_generate(text, voice)

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

    return FileResponse(video_path, media_type="video/mp4", filename="digital_human.mp4")
