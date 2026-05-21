import os
import sys
import shutil
import uuid
import torch
from pathlib import Path
from time import strftime

from api.config import SADTALKER_DIR, RESULT_DIR, UPLOAD_DIR

_models = {}


def _load():
    sys.path.insert(0, str(SADTALKER_DIR))
    from src.utils.preprocess import CropAndExtract
    from src.test_audio2coeff import Audio2Coeff
    from src.facerender.animate import AnimateFromCoeff
    from src.utils.init_path import init_path

    device = "cuda" if torch.cuda.is_available() else "cpu"
    paths = init_path(
        str(SADTALKER_DIR / "checkpoints"),
        str(SADTALKER_DIR / "src" / "config"),
        256, False, "full"
    )
    _models["preprocess"] = CropAndExtract(paths, device)
    _models["audio2coeff"] = Audio2Coeff(paths, device)
    _models["animate"] = AnimateFromCoeff(paths, device)
    _models["device"] = device
    print("[SadTalker] Models loaded")
    return _models


def _unload(_):
    _models.clear()
    print("[SadTalker] Models unloaded")


def loader():
    return _load()


def unloader(m):
    _unload(m)


def generate(image_path: str, audio_path: str, models: dict) -> str:
    sys.path.insert(0, str(SADTALKER_DIR))
    from src.generate_batch import get_data
    from src.generate_facerender_batch import get_facerender_data

    device = models["device"]
    save_dir = str(RESULT_DIR / (strftime("%Y%m%d_%H%M%S") + f"_{uuid.uuid4().hex[:6]}"))
    os.makedirs(save_dir, exist_ok=True)
    first_frame_dir = os.path.join(save_dir, "first_frame_dir")
    os.makedirs(first_frame_dir, exist_ok=True)

    first_coeff_path, crop_pic_path, crop_info = models["preprocess"].generate(
        image_path, first_frame_dir, "full", source_image_flag=True, pic_size=256
    )
    if first_coeff_path is None:
        raise RuntimeError("Failed to extract face coefficients")

    batch = get_data(first_coeff_path, audio_path, device, ref_eyeblink_coeff_path=None, still=True)
    coeff_path = models["audio2coeff"].generate(batch, save_dir, 0, None)
    data = get_facerender_data(
        coeff_path, crop_pic_path, first_coeff_path, audio_path,
        batch_size=2, input_yaw_list=None, input_pitch_list=None, input_roll_list=None,
        expression_scale=1.0, still_mode=True, preprocess="full", size=256
    )
    result = models["animate"].generate(
        data, save_dir, image_path, crop_info,
        enhancer=None, background_enhancer=None, preprocess="full", img_size=256
    )
    output_path = save_dir + ".mp4"
    shutil.move(result, output_path)
    shutil.rmtree(save_dir, ignore_errors=True)
    return output_path
