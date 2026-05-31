from collections import Counter, defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session, load_only

from app.models.audit_log import AuditLog
from app.services.audit_service import json_loads, to_audit_log_item
from app.services.risk_engine import compare_risk_levels


def get_dashboard_stats(db: Session) -> dict[str, Any]:
    logs = (
        db.query(AuditLog)
        .options(
            load_only(
                AuditLog.id,
                AuditLog.user_message,
                AuditLog.input_risk_level,
                AuditLog.output_risk_level,
                AuditLog.input_risk_types,
                AuditLog.output_risk_types,
                AuditLog.input_api_result,
                AuditLog.output_api_result,
                AuditLog.input_blocked,
                AuditLog.output_blocked,
                AuditLog.blocked_stage,
                AuditLog.reason,
                AuditLog.created_at,
            )
        )
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    total_requests = len(logs)
    input_blocked = sum(1 for log in logs if log.input_blocked)
    output_blocked = sum(1 for log in logs if log.output_blocked)
    allowed = sum(1 for log in logs if log.blocked_stage == "none")

    risk_level_distribution: Counter[str] = Counter()
    risk_type_distribution: Counter[str] = Counter()
    daily_requests: defaultdict[str, int] = defaultdict(int)
    recent_high_risk_logs: list[dict[str, Any]] = []
    api_moderation_calls = 0

    for log in logs:
        input_level = log.input_risk_level or "low"
        output_level = log.output_risk_level or "low"
        final_level = compare_risk_levels(input_level, output_level)
        risk_level_distribution[final_level] += 1

        for risk_type in set(json_loads(log.input_risk_types, []) + json_loads(log.output_risk_types, [])):
            risk_type_distribution[risk_type] += 1

        date_key = log.created_at.date().isoformat() if isinstance(log.created_at, datetime) else str(log.created_at)
        daily_requests[date_key] += 1

        if log.input_api_result:
            provider = json_loads(log.input_api_result, {}).get("provider")
            if provider and provider != "none":
                api_moderation_calls += 1
        if log.output_api_result:
            provider = json_loads(log.output_api_result, {}).get("provider")
            if provider and provider != "none":
                api_moderation_calls += 1

        if final_level in {"high", "critical"} and len(recent_high_risk_logs) < 10:
            item = to_audit_log_item(log)
            recent_high_risk_logs.append(
                {
                    "id": item.id,
                    "created_at": item.created_at.isoformat(),
                    "user_message": item.user_message,
                    "risk_level": final_level,
                    "blocked_stage": item.blocked_stage,
                    "reason": item.reason,
                }
            )

    return {
        "total_requests": total_requests,
        "input_blocked": input_blocked,
        "output_blocked": output_blocked,
        "allowed": allowed,
        "api_moderation_calls": api_moderation_calls,
        "api_moderation_count": api_moderation_calls,
        "risk_level_distribution": dict(risk_level_distribution),
        "risk_type_distribution": dict(risk_type_distribution),
        "daily_requests": [
            {"date": date, "count": count}
            for date, count in sorted(daily_requests.items())
        ],
        "recent_high_risk_logs": recent_high_risk_logs,
    }
