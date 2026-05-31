from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_reply: Mapped[str | None] = mapped_column(Text, nullable=True)

    input_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    output_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    input_risk_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_risk_types: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_rule_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_rule_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_api_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_api_result: Mapped[str | None] = mapped_column(Text, nullable=True)

    input_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    output_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_stage: Mapped[str] = mapped_column(String(20), default="none")
    action: Mapped[str] = mapped_column(String(30), default="allow")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
