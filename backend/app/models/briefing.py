from datetime import date, datetime

from sqlalchemy import Date, DateTime, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Briefing(Base):
    __tablename__ = "briefings"
    __table_args__ = (UniqueConstraint("briefing_date", "briefing_type", name="uq_briefings_date_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    briefing_date: Mapped[date] = mapped_column(Date, index=True)
    briefing_type: Mapped[str] = mapped_column(String(30), default="daily_morning")
    title: Mapped[str | None] = mapped_column(String(200))
    one_liner: Mapped[str | None] = mapped_column(Text)
    content_markdown: Mapped[str] = mapped_column(Text)
    content_sections: Mapped[dict | None] = mapped_column(JSON)
    highlighted_news_ids: Mapped[list[int] | None] = mapped_column(JSON)
    keywords: Mapped[list[str] | None] = mapped_column(JSON)
    source_article_count: Mapped[int | None] = mapped_column(default=0)
    model_used: Mapped[str | None] = mapped_column(String(50))
    tokens_used: Mapped[int | None] = mapped_column(default=0)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

