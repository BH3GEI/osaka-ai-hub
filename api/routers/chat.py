import base64

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from api.config import OLLAMA_URL

router = APIRouter()

MAX_IMAGE_BYTES = 20 * 1024 * 1024


@router.post("/api/chat")
async def chat(
    message: str = Form(...),
    model: str = Form("qwen3.6:27b"),
    stream: bool = Form(False),
    image: UploadFile = File(None),
):
    user_msg = {"role": "user", "content": message}
    if image is not None:
        data = await image.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "Image too large (max 20MB)")
        user_msg["images"] = [base64.b64encode(data).decode()]
    payload = {
        "model": model,
        "messages": [user_msg],
        "stream": stream,
    }
    if stream:
        async def _stream():
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=payload) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk
        return StreamingResponse(_stream(), media_type="application/x-ndjson")

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, f"Ollama error: {e.response.status_code}")
        except httpx.ConnectError:
            raise HTTPException(503, "Ollama service unavailable")
        return resp.json()
