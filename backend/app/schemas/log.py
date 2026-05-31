from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: int
    user_message: str | None
    model_name: str | None
    model_reply: str | None
    final_reply: str | None
    input_risk_level: str | None
    output_risk_level: str | None
    input_risk_types: list[str]
    output_risk_types: list[str]
    input_rule_result: dict[str, Any] | None
    output_rule_result: dict[str, Any] | None
    input_api_result: dict[str, Any] | None
    output_api_result: dict[str, Any] | None
    input_blocked: bool
    output_blocked: bool
    blocked_stage: str
    action: str
    reason: str | None
    latency_ms: int | None
    created_at: datetime


class AuditLogListItem(BaseModel):
    id: int
    user_message: str | None
    model_name: str | None
    final_reply: str | None
    input_risk_level: str | None
    output_risk_level: str | None
    input_risk_types: list[str]
    output_risk_types: list[str]
    input_blocked: bool
    output_blocked: bool
    blocked_stage: str
    action: str
    reason: str | None
    latency_ms: int | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogListItem]
    total: int
    page: int
    page_size: int
