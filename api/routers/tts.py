import uuid
import httpx
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse

from api.config import TTS_URL, TTS_USER, TTS_PASS, UPLOAD_DIR

router = APIRouter()


async def tts_generate(text: str, voice: str = "af_heart") -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(
                f"{TTS_URL}/api/tts",
                data={"text": text, "voice": voice},
                auth=(TTS_USER, TTS_PASS),
            )
            resp.raise_for_status()
            info = resp.json()
            audio_resp = await client.get(
                f"{TTS_URL}/api/download/{info['file']}",
                auth=(TTS_USER, TTS_PASS),
            )
            audio_resp.raise_for_status()
        except httpx.ConnectError:
            raise HTTPException(503, "TTS service unavailable")
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, f"TTS error: {e.response.status_code}")

    audio_path = str(UPLOAD_DIR / f"{uuid.uuid4().hex}.wav")
    with open(audio_path, "wb") as f:
        f.write(audio_resp.content)
    return audio_path


@router.post("/api/tts")
async def tts(
    text: str = Form(...),
    voice: str = Form("af_heart"),
):
    audio_path = await tts_generate(text, voice)
    return FileResponse(audio_path, media_type="audio/wav", filename="tts.wav")
