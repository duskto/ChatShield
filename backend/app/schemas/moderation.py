from typing import Any

from pydantic import BaseModel, Field


class MatchedRule(BaseModel):
    name: str
    keyword: str | None = None
    pattern: str | None = None
    risk_level: str
    category: str
    match_type: str = "keyword"


class DetectionResult(BaseModel):
    safe: bool = True
    risk_level: str = "low"
    risk_types: list[str] = Field(default_factory=list)
    matched_rules: list[MatchedRule] = Field(default_factory=list)
    action: str = "allow"
    reason: str = "未发现明显风险"
    provider: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    error: str | None = None

