from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .schemas import EmotionResponse
from .text_emotion import EmotionResult, analyze_text


class TextEmotionRequest(BaseModel):
    text: str = Field(..., min_length=1)


app = FastAPI(title="EmotionMirror API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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