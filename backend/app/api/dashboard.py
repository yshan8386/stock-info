from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Briefing, GlossaryTerm
from app.schemas.brief import BriefingArchiveItem
from app.schemas.dashboard import DashboardSummary, GlossarySummary, MenuStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)) -> DashboardSummary:
    today_briefing = db.scalar(
        select(Briefing).where(Briefing.briefing_date == date.today()).order_by(desc(Briefing.generated_at))
    )
    recent_terms = list(db.scalars(select(GlossaryTerm.term_ko).order_by(desc(GlossaryTerm.created_at)).limit(2)))
    total_terms = db.scalar(select(func.count(GlossaryTerm.id))) or 0
    return DashboardSummary(
        today_briefing=BriefingArchiveItem.model_validate(today_briefing) if today_briefing else None,
        backtest=MenuStatus(status="coming_soon"),
        position=MenuStatus(status="coming_soon"),
        glossary=GlossarySummary(total_terms=total_terms, recent_added=recent_terms),
    )

