from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Briefing
from app.schemas.brief import BriefingArchiveItem, BriefingOut
from app.services.briefing_generator import generate_daily_briefing

router = APIRouter(prefix="/brief", tags=["brief"])


@router.get("/today", response_model=BriefingOut)
def get_today(db: Session = Depends(get_db)) -> Briefing:
    today = date.today()
    briefing = db.scalar(
        select(Briefing).where(Briefing.briefing_date == today, Briefing.briefing_type == "daily_morning")
    )
    if briefing is None:
        briefing = db.scalar(
            select(Briefing)
            .where(Briefing.briefing_type == "daily_morning")
            .order_by(desc(Briefing.briefing_date), desc(Briefing.generated_at))
        )
    if briefing is None:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@router.get("/archive", response_model=list[BriefingArchiveItem])
def list_archive(db: Session = Depends(get_db), limit: int = 30) -> list[Briefing]:
    return list(db.scalars(select(Briefing).order_by(desc(Briefing.briefing_date)).limit(min(limit, 100))))


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
def get_by_date(briefing_date: date, db: Session = Depends(get_db)) -> Briefing:
    briefing = db.scalar(
        select(Briefing).where(Briefing.briefing_date == briefing_date, Briefing.briefing_type == "daily_morning")
    )
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
    return generate_daily_briefing(db, date.today())
