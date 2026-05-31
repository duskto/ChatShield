from pydantic import BaseModel, Field


class RiskCountItem(BaseModel):
    date: str
    count: int


class DashboardStatsResponse(BaseModel):
    total_requests: int
    input_blocked: int
    output_blocked: int
    allowed: int
    api_moderation_count: int
    risk_level_distribution: dict[str, int] = Field(default_factory=dict)
    risk_type_distribution: dict[str, int] = Field(default_factory=dict)
    daily_requests: list[RiskCountItem] = Field(default_factory=list)
    recent_high_risk_logs: list[dict] = Field(default_factory=list)

