from datetime import date, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Briefing, News


def _section_label(category: str) -> str:
    return {"dev": "개발/기술", "investment": "투자/금융", "ai": "AI/ML"}.get(category, category)


def generate_mock_markdown(news_items: list[News], target_date: date) -> tuple[str, dict, list[str]]:
    sections: dict[str, dict] = {}
    keywords: list[str] = []
    for category in ("dev", "investment", "ai"):
        category_items = [item for item in news_items if item.category == category][:5]
        highlights = [
            {"title": item.title, "url": item.url, "source": item.source_name}
            for item in category_items[:3]
        ]
        sections[category] = {
            "comment": f"{_section_label(category)} 섹션에서 {len(category_items)}건의 주요 소식을 확인했습니다.",
            "highlights": highlights,
        }
        keywords.extend([item.title.split()[0] for item in category_items[:2] if item.title.split()])

    lines = [
        f"# {target_date.strftime('%Y년 %-m월 %-d일')} 브리핑",
        "",
        "## 한 줄 요약",
        "수집된 RSS 기사를 기반으로 오늘 확인할 핵심 이슈를 정리했습니다.",
        "",
    ]
    for category in ("dev", "investment", "ai"):
        lines.append(f"## {_section_label(category)}")
        lines.append(sections[category]["comment"])
        lines.append("")
        lines.append("**주목할 기사**")
        for highlight in sections[category]["highlights"]:
            lines.append(f"- [{highlight['title']}]({highlight['url']}): {highlight['source']}")
        if not sections[category]["highlights"]:
            lines.append("- 아직 수집된 기사가 없습니다.")
        lines.append("")
    lines.append("## 오늘의 키워드")
    lines.append(", ".join(keywords[:8]) or "데이터 수집 대기")
    return "\n".join(lines), sections, keywords[:8]


def generate_daily_briefing(db: Session, target_date: date | None = None) -> Briefing:
    settings = get_settings()
    target_date = target_date or date.today()
    since = datetime.combine(target_date, datetime.min.time()) - timedelta(hours=6)
    news_items = list(
        db.scalars(select(News).where(News.collected_at >= since).order_by(desc(News.published_at))).all()
    )
    markdown, sections, keywords = generate_mock_markdown(news_items, target_date)
    one_liner = "수집된 RSS 기사를 기반으로 오늘의 핵심 이슈를 정리했습니다."
    title = f"{target_date.isoformat()} 데일리 브리핑"

    briefing = db.scalar(
        select(Briefing).where(
            Briefing.briefing_date == target_date,
            Briefing.briefing_type == "daily_morning",
        )
    )
    if briefing is None:
        briefing = Briefing(briefing_date=target_date, briefing_type="daily_morning", content_markdown=markdown)
        db.add(briefing)
    briefing.title = title
    briefing.one_liner = one_liner
    briefing.content_markdown = markdown
    briefing.content_sections = sections
    briefing.highlighted_news_ids = [item.id for item in news_items[:10]]
    briefing.keywords = keywords
    briefing.source_article_count = len(news_items)
    briefing.model_used = "mock" if settings.mock_claude else settings.claude_model
    briefing.generated_at = datetime.now()
    db.commit()
    db.refresh(briefing)
    return briefing

