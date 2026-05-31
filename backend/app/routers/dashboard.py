from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.dashboard import DashboardStatsResponse
from app.services.stats_service import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def fetch_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStatsResponse:
    return DashboardStatsResponse(**get_dashboard_stats(db))

