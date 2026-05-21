from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

# Directories on osaka (set via env or defaults)
import os

DATA_DIR = Path(os.getenv("OSAKA_DATA_DIR", str(Path.home() / "liyao")))
UPLOAD_DIR = DATA_DIR / "tmp" / "uploads"
RESULT_DIR = DATA_DIR / "tmp" / "results"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_AVATAR = ASSETS_DIR / "default_avatar.png"

SADTALKER_DIR = DATA_DIR / "SadTalker"
MUSETALK_DIR = DATA_DIR / "MuseTalk"
HALLO3_DIR = DATA_DIR / "hallo3"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
TTS_URL = os.getenv("TTS_URL", "http://127.0.0.1:18800")
TTS_USER = os.getenv("TTS_USER", "rhodes1")
TTS_PASS = os.getenv("TTS_PASS", "RhodesIsland2026TTS")

MODEL_TTL = int(os.getenv("MODEL_TTL", "600"))
