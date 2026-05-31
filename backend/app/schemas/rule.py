from datetime import datetime

from pydantic import BaseModel


class RuleItem(BaseModel):
    id: int
    name: str
    category: str
    pattern: str
    match_type: str
    risk_level: str
    enabled: bool
    description: str | None
    created_at: datetime

