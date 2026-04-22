from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Briefing
from app.schemas.brief import BriefingArchiveItem, BriefingOut
from app.services.briefing_generator import BRIEFING_TYPE_MORNING, generate_daily_briefing

router = APIRouter(prefix="/brief", tags=["brief"])


@router.get("/today", response_model=BriefingOut)
def get_today(db: Session = Depends(get_db)) -> Briefing:
    settings = get_settings()
    today = datetime.now(ZoneInfo(settings.timezone)).date()
    briefing = db.scalar(
        select(Briefing).where(Briefing.briefing_date == today).order_by(desc(Briefing.generated_at), desc(Briefing.id))
    )
    if briefing is None:
        briefing = db.scalar(
            select(Briefing)
            .order_by(desc(Briefing.briefing_date), desc(Briefing.generated_at))
        )
    if briefing is None:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@router.get("/archive", response_model=list[BriefingArchiveItem])
def list_archive(db: Session = Depends(get_db), limit: int = 30) -> list[Briefing]:
    return list(
        db.scalars(
            select(Briefing).order_by(desc(Briefing.briefing_date), desc(Briefing.generated_at), desc(Briefing.id)).limit(min(limit, 100))
        )
    )


@router.get("/search", response_model=list[BriefingArchiveItem])
def search_briefings(q: str, db: Session = Depends(get_db)) -> list[Briefing]:
    query = f"%{q}%"
    return list(
        db.scalars(
            select(Briefing)
            .where(or_(Briefing.title.ilike(query), Briefing.one_liner.ilike(query), Briefing.content_markdown.ilike(query)))
            .order_by(desc(Briefing.briefing_date))
            .limit(50)
        )
    )


@router.get("/date/{briefing_date}", response_model=BriefingOut)
def get_by_date(briefing_date: date, briefing_type: str | None = None, db: Session = Depends(get_db)) -> Briefing:
    query = select(Briefing).where(Briefing.briefing_date == briefing_date)
    if briefing_type:
        query = query.where(Briefing.briefing_type == briefing_type)
    briefing = db.scalar(query.order_by(desc(Briefing.generated_at), desc(Briefing.id)))
    if briefing is None:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@router.get("/{briefing_id}", response_model=BriefingOut)
def get_by_id(briefing_id: int, db: Session = Depends(get_db)) -> Briefing:
    briefing = db.get(Briefing, briefing_id)
    if briefing is None:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@router.post("/regenerate", response_model=BriefingOut)
def regenerate(_: object = Depends(get_current_user), db: Session = Depends(get_db)) -> Briefing:
    settings = get_settings()
    today = datetime.now(ZoneInfo(settings.timezone)).date()
    return generate_daily_briefing(db, today, BRIEFING_TYPE_MORNING)
