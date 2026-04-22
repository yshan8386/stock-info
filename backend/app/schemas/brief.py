from datetime import date, datetime

from pydantic import BaseModel


class BriefingOut(BaseModel):
    id: int
    briefing_date: date
    briefing_type: str
    title: str | None = None
    one_liner: str | None = None
    content_markdown: str
    content_sections: dict | None = None
    keywords: list[str] | None = None
    source_article_count: int | None = None
    model_used: str | None = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class BriefingArchiveItem(BaseModel):
    id: int
    briefing_date: date
    briefing_type: str
    title: str | None = None
    one_liner: str | None = None
    generated_at: datetime

    model_config = {"from_attributes": True}
