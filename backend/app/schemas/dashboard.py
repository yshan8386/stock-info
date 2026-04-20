from pydantic import BaseModel

from app.schemas.brief import BriefingArchiveItem


class MenuStatus(BaseModel):
    status: str


class GlossarySummary(BaseModel):
    total_terms: int
    recent_added: list[str]


class DashboardSummary(BaseModel):
    today_briefing: BriefingArchiveItem | None
    backtest: MenuStatus
    position: MenuStatus
    glossary: GlossarySummary

