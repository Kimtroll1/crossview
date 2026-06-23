from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.schemas.report import ReportResponse
from app.security.tokens import get_current_user
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/me", response_model=ReportResponse)
def my_report(
    period: str = Query(default="weekly", pattern="^(weekly|monthly)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ReportService().build_report(db, user, period)


@router.get("/{user_id}/weekly", response_model=ReportResponse)
def legacy_weekly_report(user_id: str, db: Session = Depends(get_db)):
    return ReportService().build_for_external_id(db, user_id, "weekly")


@router.get("/{user_id}/monthly", response_model=ReportResponse)
def legacy_monthly_report(user_id: str, db: Session = Depends(get_db)):
    return ReportService().build_for_external_id(db, user_id, "monthly")
