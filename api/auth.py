import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("OSAKA_API_KEY", "")


async def verify(x_api_key: str = Header(None)):
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(401, "Invalid or missing API key")
