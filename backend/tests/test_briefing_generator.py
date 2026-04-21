from datetime import date, datetime, timedelta

from app.models import News
from app.services.briefing_generator import _build_fallback_payload, _render_markdown, _group_ranked_news


def _news_item(
    news_id: int,
    category: str,
    title: str,
    source_name: str,
    *,
    hours_ago: int = 1,
    excerpt: str | None = None,
) -> News:
    now = datetime.now()
    return News(
        id=news_id,
        title=title,
        url=f"https://example.com/{news_id}",
        source_feed_id=None,
        source_name=source_name,
        category=category,
        author=None,
        published_at=now - timedelta(hours=hours_ago),
        content=None,
        content_excerpt=excerpt,
        raw_data=None,
        collected_at=now - timedelta(minutes=5),
    )


def test_fallback_briefing_builds_sections_and_markdown() -> None:
    items = [
        _news_item(1, "dev", "React 19 정식 출시", "React Status", excerpt="react release"),
        _news_item(2, "investment", "미국 반도체 ETF 강세", "MarketWatch", excerpt="etf move"),
        _news_item(3, "ai", "OpenAI 신규 모델 발표", "OpenAI Blog", excerpt="model launch"),
        _news_item(4, "dev", "React 19 정식 출시", "JavaScript Weekly", excerpt="duplicate title"),
    ]

    grouped = _group_ranked_news(items, datetime.now())
    payload = _build_fallback_payload(grouped, date(2026, 4, 21))
    markdown = _render_markdown(payload, date(2026, 4, 21))

    assert len(grouped["dev"]) == 1
    assert payload["one_liner"]
    assert payload["sections"]["investment"]["highlights"][0]["title"] == "미국 반도체 ETF 강세"
    assert "## 투자/금융" in markdown
    assert "## 오늘의 키워드" in markdown


def test_article_ranking_uses_relevance_and_source_diversity() -> None:
    items = [
        _news_item(10, "investment", "일반 증시 뉴스", "MarketWatch", hours_ago=1),
        _news_item(11, "investment", "FOMC 금리 환율 반도체 수출 ETF 동향", "MarketWatch", hours_ago=6),
        _news_item(12, "investment", "금리 인하 기대와 유가 변동", "MarketWatch", hours_ago=7),
        _news_item(13, "investment", "코스피 실적 반도체 투자 심리 개선", "매일경제 금융", hours_ago=8),
        _news_item(14, "investment", "나스닥 ETF 반등", "Investing.com Stock Market News", hours_ago=9),
    ]

    grouped = _group_ranked_news(items, datetime.now())
    investment_titles = [item.title for item in grouped["investment"]]

    assert investment_titles[0] == "FOMC 금리 환율 반도체 수출 ETF 동향"
    assert "일반 증시 뉴스" not in investment_titles[:3]
    assert sum(item.source_name == "MarketWatch" for item in grouped["investment"]) == 2
