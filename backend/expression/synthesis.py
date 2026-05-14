import sys
import os
import tempfile

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

_PARAM_KEYS = [
    "smile", "wink", "eyebrow",
    "eyeball_direction_x", "eyeball_direction_y",
    "lip_variation_zero", "lip_variation_one", "lip_variation_two", "lip_variation_three",
]

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


def synthesize_expression(image_path: str, emotion: str):
    """Single-frame expression synthesis."""
    import cv2

    pipeline = _get_pipeline()
    params = EMOTION_PARAMS.get(emotion, {})
    print(f"[DEBUG] emotion={emotion}, params={params}")

    import gradio as gr
    try:
        eye_r, lip_r = pipeline.init_retargeting_image(2.3, 0.0, 0.0, image_path)
    except gr.Error as e:
        if "NO face" in str(e) or "No face" in str(e):
            raise NoFaceError("未检测到人脸，请上传包含清晰正面人脸的照片") from e
        raise

    result_img = _run_retargeting(pipeline, image_path, eye_r, lip_r, params)
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
    yaw   =  2.5 * math.sin(2 * phase)
    pitch =  1.5 * math.sin(1 * phase + math.pi / 4)
    roll  =  1.0 * math.sin(3 * phase)
    return yaw, pitch, roll


def synthesize_expression_gif(image_path: str, emotion: str, num_frames: int = 12, fps: int = 10):
    """Generate a seamless loop GIF: neutral → emotion → neutral.

    The animation loops smoothly because the last frame returns to neutral.
    Subtle head micro-sway (yaw/pitch/roll) is added for a pseudo-3D effect.

    Returns:
        Path to the output GIF file.
    """
    import cv2
    import imageio
    import numpy as np
    from rembg import remove

    pipeline = _get_pipeline()
    target = EMOTION_PARAMS.get(emotion, {})

    import gradio as gr
    try:
        eye_r, lip_r = pipeline.init_retargeting_image(2.3, 0.0, 0.0, image_path)
    except gr.Error as e:
        if "NO face" in str(e) or "No face" in str(e):
            raise NoFaceError("未检测到人脸") from e
        raise

    # Generate mask from first frame using rembg
    first_img = _run_retargeting(pipeline, image_path, eye_r, lip_r, {})
    first_bgr = cv2.cvtColor(first_img, cv2.COLOR_RGB2BGR)
    mask_rgba = remove(first_bgr)  # returns BGRA
    mask = mask_rgba[:, :, 3]  # alpha channel as mask
    mask = (mask > 128).astype(np.uint8) * 255

    def apply_mask(img):
        fg = cv2.bitwise_and(img, img, mask=mask)
        bg = np.full_like(img, 255)
        bg = cv2.bitwise_and(bg, bg, mask=cv2.bitwise_not(mask))
        return cv2.add(fg, bg)

    frames = []
    math = __import__("math")
    total_frames = 2 * num_frames

    # Phase 1: neutral → target (ease-in-out)
    for i in range(num_frames):
        t = i / num_frames
        t = 0.5 - 0.5 * math.cos(t * math.pi)
        params = _interpolate_params(target, t)
        yaw, pitch, roll = _head_pose_at(i, total_frames)
        img = _run_retargeting(pipeline, image_path, eye_r, lip_r, params,
                               yaw=yaw, pitch=pitch, roll=roll)
        frames.append(apply_mask(img))

    # Phase 2: target → neutral (ease-in-out)
    for i in range(num_frames):
        t = 1.0 - (i + 1) / num_frames
        t = 0.5 - 0.5 * math.cos(t * math.pi)
        params = _interpolate_params(target, t)
        yaw, pitch, roll = _head_pose_at(num_frames + i, total_frames)
        img = _run_retargeting(pipeline, image_path, eye_r, lip_r, params,
                               yaw=yaw, pitch=pitch, roll=roll)
        frames.append(apply_mask(img))

    out_path = os.path.join(
        tempfile.gettempdir(),
        f"expr_{emotion}_anim.gif",
    )
    imageio.mimsave(out_path, frames, fps=fps, loop=0)
    return out_path
