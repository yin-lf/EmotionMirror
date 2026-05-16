import sys
import os
import tempfile
import numpy as np

_LIVEPORTRAIT_DIR = os.path.join(os.path.dirname(__file__), "LivePortrait")

EMOTION_PARAMS = {
    "开心": {"smile": 1.3, "lip_variation_two": 12, "eyeball_direction_y": -20, "eyebrow": 5},
    "悲伤": {"smile": -0.3, "eyebrow": -25, "lip_variation_three": -60, "eyeball_direction_y": 30},
    "愤怒": {"smile": -0.3, "eyebrow": -30, "lip_variation_three": -70, "lip_variation_one": -15},
    "焦虑": {"eyebrow": -20, "lip_variation_one": -12, "eyeball_direction_y": 40, "lip_variation_three": -30},
    "恐惧": {"eyebrow": 30, "lip_variation_one": 15, "eyeball_direction_y": -50, "lip_variation_three": 80},
    "平静": {},
    "厌恶": {"smile": -0.3, "eyebrow": -20, "lip_variation_zero": -0.08, "lip_variation_three": -40},
    "惊讶": {"smile": 0.5, "eyebrow": 30, "lip_variation_three": 100, "eyeball_direction_y": -40},
}

PARAM_RANGES = {
    "smile":                {"min": -1.0, "max": 1.5,  "default": 0.0,  "step": 0.1},
    "wink":                 {"min": 0.0,  "max": 1.0,  "default": 0.0,  "step": 0.05},
    "eyebrow":              {"min": -40,  "max": 40,   "default": 0.0,  "step": 1},
    "eyeball_direction_x":  {"min": -60,  "max": 60,   "default": 0.0,  "step": 1},
    "eyeball_direction_y":  {"min": -60,  "max": 60,   "default": 0.0,  "step": 1},
    "lip_variation_zero":   {"min": -0.1, "max": 0.1,  "default": 0.0,  "step": 0.005},
    "lip_variation_one":    {"min": -30,  "max": 30,   "default": 0.0,  "step": 1},
    "lip_variation_two":    {"min": -30,  "max": 30,   "default": 0.0,  "step": 1},
    "lip_variation_three":  {"min": -100, "max": 100,  "default": 0.0,  "step": 1},
}

PARAM_LABELS = {
    "smile":               "微笑",
    "wink":                "眨眼",
    "eyebrow":             "眉毛",
    "eyeball_direction_x": "眼球水平",
    "eyeball_direction_y": "眼球垂直",
    "lip_variation_zero":  "嘴唇微调",
    "lip_variation_one":   "嘴唇变化一",
    "lip_variation_two":   "嘴唇变化二",
    "lip_variation_three": "嘴唇变化三",
}

_PARAM_KEYS = list(PARAM_RANGES.keys())

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        if _LIVEPORTRAIT_DIR not in sys.path:
            sys.path.insert(0, _LIVEPORTRAIT_DIR)
        from src.config.inference_config import InferenceConfig
        from src.config.crop_config import CropConfig
        from src.config.argument_config import ArgumentConfig
        from src.gradio_pipeline import GradioPipeline

        inference_cfg = InferenceConfig()
        crop_cfg = CropConfig()
        args = ArgumentConfig(det_thresh=0.05)
        _pipeline = GradioPipeline(inference_cfg=inference_cfg, crop_cfg=crop_cfg, args=args)
        _pipeline.cropper.crop_cfg.det_thresh = 0.05
    return _pipeline


class NoFaceError(Exception):
    pass


_rembg_warmed = False


def warmup_rembg():
    global _rembg_warmed
    if _rembg_warmed:
        return
    from rembg import remove
    dummy = np.zeros((100, 100, 3), dtype=np.uint8)
    remove(dummy)
    _rembg_warmed = True


def _run_retargeting(pipeline, image_path, eye_ratio, lip_ratio, params,
                     yaw=0.0, pitch=0.0, roll=0.0):
    """Run expression retargeting with given parameter dict and head pose."""
    import gradio as gr

    try:
        _, result_img = pipeline.execute_image_retargeting(
            input_eye_ratio=eye_ratio,
            input_lip_ratio=lip_ratio,
            input_head_pitch_variation=pitch,
            input_head_yaw_variation=yaw,
            input_head_roll_variation=roll,
            mov_x=0.0,
            mov_y=0.0,
            mov_z=1.0,
            smile=params.get("smile", 0.0),
            wink=params.get("wink", 0.0),
            eyebrow=params.get("eyebrow", 0.0),
            eyeball_direction_x=params.get("eyeball_direction_x", 0.0),
            eyeball_direction_y=params.get("eyeball_direction_y", 0.0),
            lip_variation_zero=params.get("lip_variation_zero", 0.0),
            lip_variation_one=params.get("lip_variation_one", 0.0),
            lip_variation_two=params.get("lip_variation_two", 0.0),
            lip_variation_three=params.get("lip_variation_three", 0.0),
            input_image=image_path,
            retargeting_source_scale=2.3,
            flag_stitching_retargeting_input=True,
            flag_do_crop_input_retargeting_image=True,
        )
    except gr.Error as e:
        msg = str(e)
        if "NO face" in msg or "No face" in msg:
            raise NoFaceError("未检测到人脸") from e
        raise
    return result_img


def _interpolate_params(target, t):
    """Linearly interpolate params from 0 (neutral) to target at t in [0,1]."""
    return {k: v * t for k, v in target.items()}


def _apply_intensity(base_params: dict, intensity: int) -> dict:
    """Scale all expression params by intensity/5."""
    if not base_params or intensity >= 5:
        return base_params
    s = max(1, min(5, intensity)) / 5.0
    return {k: v * s for k, v in base_params.items()}


def synthesize_expression(image_path: str, emotion: str, params: dict = None, intensity: int = 5):
    """Single-frame expression synthesis."""
    import cv2

    pipeline = _get_pipeline()
    base = EMOTION_PARAMS.get(emotion, {})
    base = _apply_intensity(base, intensity)
    merged = {**base, **params} if params else base
    print(f"[DEBUG] emotion={emotion}, params={merged}")

    import gradio as gr
    try:
        eye_r, lip_r = pipeline.init_retargeting_image(2.3, 0.0, 0.0, image_path)
    except gr.Error as e:
        if "NO face" in str(e) or "No face" in str(e):
            raise NoFaceError("未检测到人脸，请上传包含清晰正面人脸的照片") from e
        raise

    result_img = _run_retargeting(pipeline, image_path, eye_r, lip_r, merged)
    out_path = os.path.join(tempfile.gettempdir(), f"expr_{emotion}_{os.path.basename(image_path)}")
    cv2.imwrite(out_path, cv2.cvtColor(result_img, cv2.COLOR_RGB2BGR))
    return out_path


def _head_pose_at(frame_idx, total_frames):
    """Compute subtle head micro-sway (yaw/pitch/roll) for pseudo-3D effect.

    Uses integer-multiple sine frequencies so the pose is identical at
    frame 0 and frame total_frames → seamless GIF loop.
    """
    import math
    phase = 2.0 * math.pi * frame_idx / total_frames
    yaw   =  1.2 * math.sin(1 * phase)
    pitch =  0.8 * math.sin(1 * phase + math.pi / 4)
    roll  =  0.5 * math.sin(1 * phase)
    return yaw, pitch, roll


def synthesize_expression_gif(image_path: str, emotion: str, num_frames: int = 12, fps: int = 10, params: dict = None, intensity: int = 5):
    """Generate a seamless loop GIF with transparent background.

    The animation loops smoothly because the last frame returns to neutral.
    Subtle head micro-sway (yaw/pitch/roll) is added for a pseudo-3D effect.
    Background is made transparent using rembg on the first frame.

    Returns:
        Path to the output GIF file.
    """
    import cv2
    import numpy as np
    from rembg import remove

    pipeline = _get_pipeline()
    base = EMOTION_PARAMS.get(emotion, {})
    base = _apply_intensity(base, intensity)
    target = {**base, **params} if params else base

    import gradio as gr
    try:
        eye_r, lip_r = pipeline.init_retargeting_image(2.3, 0.0, 0.0, image_path)
    except gr.Error as e:
        if "NO face" in str(e) or "No face" in str(e):
            raise NoFaceError("未检测到人脸") from e
        raise

    first_img = _run_retargeting(pipeline, image_path, eye_r, lip_r, {})
    first_bgr = cv2.cvtColor(first_img, cv2.COLOR_RGB2BGR)

    dilate_kernel = None
    original_height = first_bgr.shape[0]
    if original_height >= 200:
        ksize = max(3, int(original_height * 0.025) | 1)
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))

    mask_rgba = remove(first_bgr)
    mask = mask_rgba[:, :, 3]
    mask_bool = mask > 64

    if dilate_kernel is not None:
        mask_bool = cv2.dilate(mask_bool.astype(np.uint8), dilate_kernel, iterations=2).astype(bool)

    def extract_foreground(img):
        """Return RGBA image with transparent background."""
        rgba = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
        rgba[~mask_bool, 3] = 0
        return rgba

    frames_rgba = []
    math = __import__("math")
    total_frames = 2 * num_frames

    for i in range(num_frames):
        t = i / num_frames
        t = 0.5 - 0.5 * math.cos(t * math.pi)
        params = _interpolate_params(target, t)
        yaw, pitch, roll = _head_pose_at(i, total_frames)
        img = _run_retargeting(pipeline, image_path, eye_r, lip_r, params,
                               yaw=yaw, pitch=pitch, roll=roll)
        frames_rgba.append(extract_foreground(img))

    for i in range(num_frames):
        t = 1.0 - (i + 1) / num_frames
        t = 0.5 - 0.5 * math.cos(t * math.pi)
        params = _interpolate_params(target, t)
        yaw, pitch, roll = _head_pose_at(num_frames + i, total_frames)
        img = _run_retargeting(pipeline, image_path, eye_r, lip_r, params,
                               yaw=yaw, pitch=pitch, roll=roll)
        frames_rgba.append(extract_foreground(img))

    # Save as transparent GIF via PIL
    from PIL import Image

    # First frame: use its alpha to build a static mask
    mask_bool = frames_rgba[0][:, :, 3] > 128

    out_path = os.path.join(
        tempfile.gettempdir(),
        f"expr_{emotion}_anim.gif",
    )

    pil_out = []
    for arr in frames_rgba:
        rgb = arr[:, :, :3]  # RGB only
        alpha = arr[:, :, 3] > 128
        img = Image.fromarray(rgb, "RGB")
        # Quantize to 255 colors (indexes 0-254)
        p = img.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
        pal = p.getpalette()
        pal.extend([0] * (768 - len(pal)))
        p.putpalette(pal)
        # Remap transparent pixels to index 255
        arr_p = np.array(p, dtype=np.uint8)
        arr_p[~alpha] = 255
        p2 = Image.fromarray(arr_p, "P")
        p2.putpalette(pal)
        p2.info["transparency"] = 255
        pil_out.append(p2)

    pil_out[0].save(
        out_path,
        save_all=True,
        append_images=pil_out[1:],
        duration=1000 // fps,
        loop=0,
        transparency=255,
        disposal=2,
    )
    return out_path
