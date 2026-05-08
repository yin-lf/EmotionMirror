from pydantic import BaseModel, Field


class EmotionResponse(BaseModel):
    emotion: str = Field(..., description="情绪标签")
    vector: list[float] = Field(
        ..., min_length=3, max_length=3, description="V-A-D 向量，范围 [0,1]"
    )