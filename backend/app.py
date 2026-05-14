from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import tempfile
import os

from .schemas import EmotionResponse
from .text_emotion import EmotionResult, analyze_text
from .voice_emotion import analyze_voice
from .expression import synthesize_expression, synthesize_expression_gif, NoFaceError


class TextEmotionRequest(BaseModel):
    text: str = Field(..., min_length=1)


app = FastAPI(title="EmotionMirror API", version="0.1.0")

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
        from fastapi import HTTPException
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
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(temp_path)


UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "emotionmirror_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


emoji_static_dir = os.path.join(os.path.dirname(__file__), "expression", "dynamic-emoji-generator")
app.mount("/emoji-generator", StaticFiles(directory=emoji_static_dir), name="emoji-generator")