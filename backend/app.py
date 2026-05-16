import os
import json
import random
import tempfile
import urllib.request
from contextlib import asynccontextmanager

# Load .env file from project root
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.isfile(_env_path):
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _key, _val = _line.split("=", 1)
            _key, _val = _key.strip(), _val.strip().strip("\"'")
            if _key and _val:
                os.environ.setdefault(_key, _val)

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .schemas import EmotionResponse
from .text_emotion import EmotionResult, analyze_text
from .voice_emotion import analyze_voice
from .expression import synthesize_expression, synthesize_expression_gif, NoFaceError, warmup_rembg


class TextEmotionRequest(BaseModel):
    text: str = Field(..., min_length=1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    warmup_rembg()
    yield


app = FastAPI(title="EmotionMirror API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/text-emotion", response_model=EmotionResponse)
def text_emotion(payload: TextEmotionRequest) -> EmotionResult:
    return analyze_text(payload.text)


@app.post("/api/voice-emotion", response_model=EmotionResponse)
def voice_emotion(audio: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        temp_file.write(audio.file.read())
        temp_path = temp_file.name
    
    try:
        result = analyze_voice(temp_path)
        return {"emotion": result.emotion_name, "vector": result.vector}
    finally:
        os.unlink(temp_path)


@app.post("/api/expression-synthesis")
def expression_synthesis(image: UploadFile = File(...), emotion: str = Form("平静")):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        temp_file.write(image.file.read())
        temp_path = temp_file.name

    try:
        out_path = synthesize_expression(temp_path, emotion)
        return FileResponse(out_path, media_type="image/png", filename=f"expr_{emotion}.png")
    except NoFaceError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(temp_path)


@app.post("/api/expression-gif")
def expression_gif(image: UploadFile = File(...), emotion: str = Form("平静")):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
        temp_file.write(image.file.read())
        temp_path = temp_file.name

    try:
        out_path = synthesize_expression_gif(temp_path, emotion)
        return FileResponse(out_path, media_type="image/gif", filename=f"expr_{emotion}.gif")
    except NoFaceError as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(temp_path)


UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "emotionmirror_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DESKTOP_WIDGET_DIR = os.path.join(UPLOAD_DIR, "desktop_widgets")
os.makedirs(DESKTOP_WIDGET_DIR, exist_ok=True)

DESKTOP_WIDGET_GIF = os.path.join(DESKTOP_WIDGET_DIR, "default.gif")
DESKTOP_WIDGET_META = os.path.join(DESKTOP_WIDGET_DIR, "default.json")


def _sanitize_filename(name: str) -> str:
    import re
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(".")
    name = name[:64]
    return name or "default"


@app.post("/api/avatar/upload")
def avatar_upload(image: UploadFile = File(...)):
    suffix = os.path.splitext(image.filename or "image.png")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=UPLOAD_DIR) as f:
        f.write(image.file.read())
        filename = os.path.basename(f.name)
    return {"url": f"/api/avatar/file/{filename}", "filename": filename}


@app.get("/api/avatar/file/{filename}")
def avatar_file(filename: str):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@app.post("/api/desktop/publish")
def desktop_publish(emotion: str = Form(""), gif: UploadFile = File(...)):
    """Store a GIF for a specific emotion. The desktop pet displays all published emotion GIFs."""
    raw = gif.file.read()
    if len(raw) < 64:
        raise HTTPException(status_code=400, detail="Invalid or empty GIF")
    safe = _sanitize_filename(emotion) if emotion.strip() else "default"
    gif_path = os.path.join(DESKTOP_WIDGET_DIR, f"{safe}.gif")
    meta_path = os.path.join(DESKTOP_WIDGET_DIR, f"{safe}.json")
    with open(gif_path, "wb") as f:
        f.write(raw)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"emotion": emotion or ""}, f, ensure_ascii=False)
    # Also update default files for backward compatibility (single-GIF desktop pet)
    if safe != "default":
        with open(DESKTOP_WIDGET_GIF, "wb") as f:
            f.write(raw)
        with open(DESKTOP_WIDGET_META, "w", encoding="utf-8") as f:
            json.dump({"emotion": emotion or ""}, f, ensure_ascii=False)
    return {"ok": True, "emotion": emotion or "default"}


@app.get("/api/desktop/emotions")
def desktop_emotions():
    """List all available emotion GIFs with etags for the desktop pet."""
    results = []
    if not os.path.isdir(DESKTOP_WIDGET_DIR):
        return {"emotions": results}
    for fname in os.listdir(DESKTOP_WIDGET_DIR):
        if not fname.endswith(".gif"):
            continue
        gif_path = os.path.join(DESKTOP_WIDGET_DIR, fname)
        if os.path.getsize(gif_path) < 64:
            continue
        emotion_key = fname[:-4]
        meta_path = os.path.join(DESKTOP_WIDGET_DIR, f"{emotion_key}.json")
        emotion_label = ""
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, encoding="utf-8") as f:
                    emotion_label = (json.load(f).get("emotion") or "").strip()
            except (json.JSONDecodeError, OSError):
                pass
        results.append({
            "emotion": emotion_label or emotion_key,
            "key": emotion_key,
            "etag": str(int(os.path.getmtime(gif_path) * 1000)),
        })
    return {"emotions": results}


@app.get("/api/desktop/status")
def desktop_status():
    has_gif = os.path.isfile(DESKTOP_WIDGET_GIF) and os.path.getsize(DESKTOP_WIDGET_GIF) > 64
    emotion = ""
    etag = ""
    if has_gif:
        etag = str(int(os.path.getmtime(DESKTOP_WIDGET_GIF) * 1000))
        if os.path.isfile(DESKTOP_WIDGET_META):
            try:
                with open(DESKTOP_WIDGET_META, encoding="utf-8") as f:
                    emotion = (json.load(f).get("emotion") or "").strip()
            except (json.JSONDecodeError, OSError):
                emotion = ""
    return {"has_gif": has_gif, "emotion": emotion, "etag": etag}


@app.get("/api/desktop/widget.gif")
def desktop_widget_gif(emotion: str = ""):
    """Get a specific emotion GIF. If emotion is empty, returns the default (most recent)."""
    if emotion:
        safe = _sanitize_filename(emotion)
        gif_path = os.path.join(DESKTOP_WIDGET_DIR, f"{safe}.gif")
    else:
        gif_path = DESKTOP_WIDGET_GIF
    if not os.path.isfile(gif_path):
        raise HTTPException(status_code=404, detail="No GIF published yet")
    return FileResponse(gif_path, media_type="image/gif", filename=f"{emotion or 'widget'}.gif")


@app.post("/api/desktop/clear")
def desktop_clear():
    """Clear all stored desktop GIFs."""
    if os.path.isdir(DESKTOP_WIDGET_DIR):
        for fname in os.listdir(DESKTOP_WIDGET_DIR):
            try:
                os.unlink(os.path.join(DESKTOP_WIDGET_DIR, fname))
            except OSError:
                pass
    return {"ok": True}


emoji_static_dir = os.path.join(os.path.dirname(__file__), "expression", "dynamic-emoji-generator")
app.mount("/emoji-generator", StaticFiles(directory=emoji_static_dir), name="emoji-generator")

# ---------------------------------------------------------------------------
# Desktop Chat — emotion analysis + auto GIF generation + reply
# ---------------------------------------------------------------------------

SOYO_PHOTO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "soyo.jpg")

# ---------------------------------------------------------------------------
# LLM configuration (set via environment variables)
# ---------------------------------------------------------------------------
# LLM_API_URL = https://api.openai.com/v1/chat/completions
# LLM_API_KEY = sk-...
# LLM_MODEL  = gpt-4o-mini  (optional, default: gpt-4o-mini)

_LLM_URL = os.environ.get("LLM_API_URL") or os.environ.get("LLM_BASE_URL") or ""
_LLM_URL = _LLM_URL.strip().rstrip("/")
if _LLM_URL and not _LLM_URL.endswith("/chat/completions"):
    _LLM_URL += "/chat/completions"
_LLM_KEY = os.environ.get("LLM_API_KEY", "").strip()
_LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini").strip()

# ---------------------------------------------------------------------------
# Preset replies config (loaded from JSON, skip LLM when mock_enabled)
# ---------------------------------------------------------------------------
_PRESETS_PATH = os.environ.get("PRESETS_PATH", "").strip()
if not _PRESETS_PATH:
    _PRESETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets", "chat_presets.json")

_PRESETS = {
    "mock_enabled": True,
    "replies": {},
    "fallback": "\u554a\u554a\u554a\uff0c\u6211\u5728\u542c\uff0c\u4f60\u7ee7\u7eed\u8bf4\uff5e",
    "system_prompt": "你是一个名为 Soyo 的桌面宠物，正在和朋友聊天。根据对方表达的情绪（开心/悲伤/愤怒/焦虑/恐惧/平静/厌恶/惊讶）以及他说的话，用温柔可爱的语气回复，一句话即可。",
}
if os.path.isfile(_PRESETS_PATH):
    try:
        with open(_PRESETS_PATH, encoding="utf-8") as _f:
            _PRESETS.update(json.load(_f))
    except (json.JSONDecodeError, OSError) as _e:
        print(f"[Soyo] 预设文件加载失败: {_e}")
print(f"[Soyo] mock_enabled = {_PRESETS.get('mock_enabled')}, LLM_URL = {'已设置' if _LLM_URL else '未设置'}, LLM_KEY = {'已设置' if _LLM_KEY else '未设置'}")


# Conversation history for LLM context
_CONVERSATION: list[dict] = []
_MAX_HISTORY = 10


def _llm_reply(emotion: str, text: str) -> str | None:
    """Call external LLM API (OpenAI-compatible) to generate a reply.

    Returns None if LLM is not configured or the call fails,
    so the caller can fall back to template replies.
    """
    if not _LLM_URL or not _LLM_KEY:
        return None

    system_prompt = _PRESETS.get(
        "system_prompt",
        "你是一个名为 Soyo 的桌面宠物，正在和朋友聊天。"
        "根据对方表达的情绪（开心/悲伤/愤怒/焦虑/恐惧/平静/厌恶/惊讶）"
        "以及他说的话，用温柔可爱的语气回复，一句话即可。",
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_CONVERSATION[-_MAX_HISTORY:])
    messages.append({"role": "user", "content": f"[情绪: {emotion}] {text}"})

    payload = json.dumps({
        "model": _LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 120,
    }).encode("utf-8")

    req = urllib.request.Request(
        _LLM_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_LLM_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        reply = data["choices"][0]["message"]["content"].strip()
    except Exception as _e:
        print(f"[Soyo] LLM 调用失败: {_e}")
        import traceback
        traceback.print_exc()
        return None

    # Store exchange in conversation history
    _CONVERSATION.append({"role": "user", "content": f"[情绪: {emotion}] {text}"})
    if reply:
        _CONVERSATION.append({"role": "assistant", "content": reply})

    return reply if reply else None


def _chat_reply(emotion: str, text: str) -> str:
    """Generate a reply — uses presets if mock_enabled, otherwise tries LLM first."""
    replies = _PRESETS.get("replies", {})

    if _PRESETS.get("mock_enabled", True):
        options = replies.get(emotion) or replies.get("平静") or [_PRESETS["fallback"]]
        return random.choice(options)

    llm_reply = _llm_reply(emotion, text)
    if llm_reply:
        return llm_reply

    options = replies.get(emotion) or [_PRESETS["fallback"]]
    return random.choice(options)


import threading


def _generate_gif_background(emotion: str) -> None:
    """Generate and publish GIF in a background thread."""
    if not os.path.isfile(SOYO_PHOTO):
        return
    try:
        gif_path = synthesize_expression_gif(SOYO_PHOTO, emotion)
        with open(gif_path, "rb") as f:
            gif_data = f.read()
        if len(gif_data) >= 64:
            safe = _sanitize_filename(emotion)
            with open(os.path.join(DESKTOP_WIDGET_DIR, f"{safe}.gif"), "wb") as f:
                f.write(gif_data)
            with open(DESKTOP_WIDGET_GIF, "wb") as f:
                f.write(gif_data)
    except NoFaceError:
        pass


@app.post("/api/desktop/chat")
def desktop_chat(payload: TextEmotionRequest):
    """Receive chat text → reply immediately → generate GIF in background."""
    text = payload.text

    # 1. Emotion analysis
    result: EmotionResult = analyze_text(text)
    emotion = result.emotion

    # 2. Start GIF generation in background (reply won't wait for it)
    if emotion != "平静":
        threading.Thread(target=_generate_gif_background, args=(emotion,), daemon=True).start()

    # 3. Generate reply (fast: template or LLM)
    reply = _chat_reply(emotion, text)

    return {
        "emotion": emotion,
        "vector": list(result.vector),
        "reply": reply,
        "gif_published": False,
    }