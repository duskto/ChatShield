from pydantic import BaseModel, Field

from app.schemas.moderation import DetectionResult


class ChatHistoryItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ModerationContextItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=240)


class ModerationContextState(BaseModel):
    messages: list[ModerationContextItem] = Field(default_factory=list, max_length=8)
    recent_risk_types: list[str] = Field(default_factory=list, max_length=8)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=12)
    context_state: ModerationContextState | None = None


class ChatResponse(BaseModel):
    success: bool
    blocked: bool
    blocked_stage: str
    message: str
    reply: str
    model: str
    input_detection: DetectionResult
    output_detection: DetectionResult | None = None
    context_state: ModerationContextState
