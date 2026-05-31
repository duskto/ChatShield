from datetime import datetime

from pydantic import BaseModel, Field


class RuleBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    pattern: str = Field(min_length=1, max_length=1000)
    match_type: str = Field(default="keyword", pattern="^(keyword|regex)$")
    risk_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    enabled: bool = True
    description: str | None = Field(default=None, max_length=2000)


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    pattern: str | None = Field(default=None, min_length=1, max_length=1000)
    match_type: str | None = Field(default=None, pattern="^(keyword|regex)$")
    risk_level: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    enabled: bool | None = None
    description: str | None = Field(default=None, max_length=2000)


class RuleItem(RuleBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
