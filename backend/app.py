from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tempfile
import os

from .schemas import EmotionResponse
from .text_emotion import EmotionResult, analyze_text
from .voice_emotion import analyze_voice


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