import os
import uuid
import shutil
import subprocess
from pathlib import Path

from api.config import MUSETALK_DIR, RESULT_DIR


def generate(image_path: str, audio_path: str) -> str:
    work_id = uuid.uuid4().hex[:8]
    work_dir = f"/tmp/musetalk_{work_id}"
    os.makedirs(work_dir, exist_ok=True)

    abs_image = os.path.abspath(image_path)
    abs_audio = os.path.abspath(audio_path)
    video_path = os.path.join(work_dir, "input.mp4")

    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", abs_image,
        "-i", abs_audio, "-shortest",
        "-vf", "scale=512:512", "-pix_fmt", "yuv420p", "-r", "25",
        video_path
    ], capture_output=True, check=True)

    config_path = os.path.join(work_dir, "config.yaml")
    with open(config_path, "w") as f:
        f.write(f'task_0:\n video_path: "{video_path}"\n audio_path: "{abs_audio}"\n')

    out_dir = f"{work_dir}/out"
    env = os.environ.copy()
    env["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = "0"

    python_bin = str(MUSETALK_DIR / ".venv" / "bin" / "python3")
    result = subprocess.run(
        [
            python_bin, "-c",
            "import torch\n"
            "_o=torch.load\n"
            "def _p(*a,**k):k.setdefault('weights_only',False);return _o(*a,**k)\n"
            "torch.load=_p\n"
            "import runpy,sys\n"
            f"sys.argv=['inf','--inference_config','{config_path}',"
            f"'--result_dir','{out_dir}',"
            "'--unet_model_path','models/musetalkV15/unet.pth',"
            "'--unet_config','models/musetalkV15/musetalk.json',"
            "'--version','v15']\n"
            "runpy.run_module('scripts.inference',run_name='__main__')"
        ],
        cwd=str(MUSETALK_DIR),
        env=env, capture_output=True, timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"MuseTalk failed: {result.stderr[-500:]}")

    out_files = list(Path(f"{out_dir}/v15").glob("*.mp4"))
    if not out_files:
        raise RuntimeError("MuseTalk produced no output")

    final = str(RESULT_DIR / f"musetalk_{work_id}.mp4")
    shutil.copy(str(out_files[0]), final)
    shutil.rmtree(work_dir, ignore_errors=True)
    return final
