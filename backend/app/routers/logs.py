from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.log import AuditLogListResponse
from app.services.audit_service import get_audit_log_by_id, list_audit_logs, to_audit_log_item, to_audit_log_list_item

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=AuditLogListResponse)
def get_logs(
    risk_level: str | None = None,
    risk_type: str | None = None,
    blocked_stage: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    items, total = list_audit_logs(
        db=db,
        risk_level=risk_level,
        risk_type=risk_type,
        blocked_stage=blocked_stage,
        start_time=start_time,
        end_time=end_time,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        items=[to_audit_log_list_item(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}")
def get_log_detail(log_id: int, db: Session = Depends(get_db)) -> dict:
    log = get_audit_log_by_id(db, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    return to_audit_log_item(log).model_dump()
