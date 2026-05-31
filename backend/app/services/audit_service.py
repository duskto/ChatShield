import json
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.log import AuditLogItem


def json_dumps(data: Any) -> str | None:
    if data is None:
        return None
    return json.dumps(data, ensure_ascii=False)


def json_loads(data: str | None, default: Any) -> Any:
    if not data:
        return default
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return default


def create_audit_log(db: Session, payload: dict[str, Any]) -> AuditLog:
    log = AuditLog(
        user_message=payload.get("user_message"),
        model_name=payload.get("model_name"),
        model_reply=payload.get("model_reply"),
        final_reply=payload.get("final_reply"),
        input_risk_level=payload.get("input_risk_level"),
        output_risk_level=payload.get("output_risk_level"),
        input_risk_types=json_dumps(payload.get("input_risk_types", [])),
        output_risk_types=json_dumps(payload.get("output_risk_types", [])),
        input_rule_result=json_dumps(payload.get("input_rule_result")),
        output_rule_result=json_dumps(payload.get("output_rule_result")),
        input_api_result=json_dumps(payload.get("input_api_result")),
        output_api_result=json_dumps(payload.get("output_api_result")),
        input_blocked=payload.get("input_blocked", False),
        output_blocked=payload.get("output_blocked", False),
        blocked_stage=payload.get("blocked_stage", "none"),
        action=payload.get("action", "allow"),
        reason=payload.get("reason"),
        latency_ms=payload.get("latency_ms"),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def to_audit_log_item(log: AuditLog) -> AuditLogItem:
    return AuditLogItem(
        id=log.id,
        user_message=log.user_message,
        model_name=log.model_name,
        model_reply=log.model_reply,
        final_reply=log.final_reply,
        input_risk_level=log.input_risk_level,
        output_risk_level=log.output_risk_level,
        input_risk_types=json_loads(log.input_risk_types, []),
        output_risk_types=json_loads(log.output_risk_types, []),
        input_rule_result=json_loads(log.input_rule_result, None),
        output_rule_result=json_loads(log.output_rule_result, None),
        input_api_result=json_loads(log.input_api_result, None),
        output_api_result=json_loads(log.output_api_result, None),
        input_blocked=log.input_blocked,
        output_blocked=log.output_blocked,
        blocked_stage=log.blocked_stage,
        action=log.action,
        reason=log.reason,
        latency_ms=log.latency_ms,
        created_at=log.created_at,
    )


def list_audit_logs(
    db: Session,
    risk_level: str | None = None,
    risk_type: str | None = None,
    blocked_stage: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[AuditLog], int]:
    query = db.query(AuditLog)

    if risk_level:
        query = query.filter(
            or_(
                AuditLog.input_risk_level == risk_level,
                AuditLog.output_risk_level == risk_level,
            )
        )
    if risk_type:
        query = query.filter(
            or_(
                AuditLog.input_risk_types.like(f"%{risk_type}%"),
                AuditLog.output_risk_types.like(f"%{risk_type}%"),
            )
        )
    if blocked_stage:
        query = query.filter(AuditLog.blocked_stage == blocked_stage)
    if start_time:
        query = query.filter(AuditLog.created_at >= start_time)
    if end_time:
        query = query.filter(AuditLog.created_at <= end_time)
    if keyword:
        like_expr = f"%{keyword}%"
        query = query.filter(
            or_(
                AuditLog.user_message.like(like_expr),
                AuditLog.model_reply.like(like_expr),
                AuditLog.final_reply.like(like_expr),
                AuditLog.reason.like(like_expr),
            )
        )

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_audit_log_by_id(db: Session, log_id: int) -> AuditLog | None:
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()

