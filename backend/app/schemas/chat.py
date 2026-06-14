from pydantic import BaseModel, Field

from app.schemas.moderation import DetectionResult


class ChatHistoryItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=12)


class ChatResponse(BaseModel):
    success: bool
    blocked: bool
    blocked_stage: str
    message: str
    reply: str
    model: str
    input_detection: DetectionResult
    output_detection: DetectionResult | None = None
