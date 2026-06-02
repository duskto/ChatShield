from collections import Counter
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services.audit_service import json_loads


def _risk_rank_expr(column) -> Any:
    return case(
        (column == "critical", 3),
        (column == "high", 2),
        (column == "medium", 1),
        else_=0,
    )


def _final_risk_level_expr() -> Any:
    input_rank = _risk_rank_expr(AuditLog.input_risk_level)
    output_rank = _risk_rank_expr(AuditLog.output_risk_level)
    final_rank = case((input_rank >= output_rank, input_rank), else_=output_rank)
    return case(
        (final_rank == 3, "critical"),
        (final_rank == 2, "high"),
        (final_rank == 1, "medium"),
        else_="low",
    )


def get_dashboard_stats(db: Session) -> dict[str, Any]:
    final_risk_level = _final_risk_level_expr()
    request_date = func.date(AuditLog.created_at)

    totals = (
        db.query(
            func.count(AuditLog.id).label("total_requests"),
            func.coalesce(func.sum(case((AuditLog.input_blocked.is_(True), 1), else_=0)), 0).label("input_blocked"),
            func.coalesce(func.sum(case((AuditLog.output_blocked.is_(True), 1), else_=0)), 0).label("output_blocked"),
            func.coalesce(func.sum(case((AuditLog.blocked_stage == "none", 1), else_=0)), 0).label("allowed"),
        )
        .one()
    )

    risk_level_rows = (
        db.query(
            final_risk_level.label("risk_level"),
            func.count(AuditLog.id).label("count"),
        )
        .group_by(final_risk_level)
        .all()
    )
    risk_level_distribution = {row.risk_level: row.count for row in risk_level_rows if row.count}

    daily_rows = (
        db.query(
            request_date.label("date"),
            func.count(AuditLog.id).label("count"),
        )
        .group_by(request_date)
        .order_by(request_date)
        .all()
    )

    recent_high_risk_rows = (
        db.query(
            AuditLog.id,
            AuditLog.created_at,
            AuditLog.user_message,
            AuditLog.blocked_stage,
            AuditLog.reason,
            final_risk_level.label("risk_level"),
        )
        .filter(final_risk_level.in_(["high", "critical"]))
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_high_risk_logs = [
        {
            "id": row.id,
            "created_at": row.created_at.isoformat(),
            "user_message": row.user_message,
            "risk_level": row.risk_level,
            "blocked_stage": row.blocked_stage,
            "reason": row.reason,
        }
        for row in recent_high_risk_rows
    ]

    detail_rows = db.query(
        AuditLog.input_risk_types,
        AuditLog.output_risk_types,
        AuditLog.input_api_result,
        AuditLog.output_api_result,
    ).all()

    risk_type_distribution: Counter[str] = Counter()
    api_moderation_calls = 0
    for row in detail_rows:
        risk_types = set(json_loads(row.input_risk_types, []) + json_loads(row.output_risk_types, []))
        for risk_type in risk_types:
            risk_type_distribution[risk_type] += 1

        input_provider = json_loads(row.input_api_result, {}).get("provider")
        if input_provider and input_provider != "none":
            api_moderation_calls += 1

        output_provider = json_loads(row.output_api_result, {}).get("provider")
        if output_provider and output_provider != "none":
            api_moderation_calls += 1

    return {
        "total_requests": totals.total_requests,
        "input_blocked": totals.input_blocked,
        "output_blocked": totals.output_blocked,
        "allowed": totals.allowed,
        "api_moderation_calls": api_moderation_calls,
        "api_moderation_count": api_moderation_calls,
        "risk_level_distribution": risk_level_distribution,
        "risk_type_distribution": dict(risk_type_distribution),
        "daily_requests": [{"date": row.date, "count": row.count} for row in daily_rows],
        "recent_high_risk_logs": recent_high_risk_logs,
    }
