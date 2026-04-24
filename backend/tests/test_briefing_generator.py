from datetime import date, datetime, timedelta

from app.models import News
from app.services.briefing_generator import (
    BRIEFING_TYPE_AFTERNOON,
    BRIEFING_TYPE_MORNING,
    _article_based_highlight_summary,
    _briefing_window,
    _build_fallback_payload,
    _categories_needing_backfill,
    _group_ranked_news,
    _prompt_articles,
    _render_markdown,
    _sanitize_payload,
)


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
        content_excerpt=excerpt,
        raw_data=None,
        collected_at=now - timedelta(minutes=5),
    )


def _news_item_with_article_text(
    news_id: int,
    category: str,
    title: str,
    source_name: str,
    article_text: str,
) -> News:
    item = _news_item(news_id, category, title, source_name, excerpt="RSS 요약")
    item.raw_data = {"article_text": article_text}
    return item


def test_fallback_briefing_builds_sections_and_markdown() -> None:
    items = [
        _news_item(
            1, "dev", "React 19 정식 출시", "React Status", excerpt="react release"
        ),
        _news_item(
            2, "investment", "미국 반도체 ETF 강세", "MarketWatch", excerpt="etf move"
        ),
        _news_item(
            3, "ai", "OpenAI 신규 모델 발표", "OpenAI Blog", excerpt="model launch"
        ),
        _news_item(
            4,
            "dev",
            "React 19 정식 출시",
            "JavaScript Weekly",
            excerpt="duplicate title",
        ),
    ]

    grouped = _group_ranked_news(items, datetime.now())
    payload = _build_fallback_payload(grouped, date(2026, 4, 21))
    markdown = _render_markdown(payload, date(2026, 4, 21))

    assert len(grouped["dev"]) == 1
    assert payload["one_liner"]
    assert (
        payload["sections"]["investment"]["highlights"][0]["title"]
        == "미국 반도체 ETF 강세"
    )
    assert payload["sections"]["investment"]["highlights"][0]["summary"]
    assert "## 투자/금융" in markdown
    assert "## 오늘의 키워드" in markdown


def test_briefing_windows_use_korean_market_day_boundaries() -> None:
    morning_start, morning_end = _briefing_window(
        date(2026, 4, 22), BRIEFING_TYPE_MORNING, "Asia/Seoul"
    )
    afternoon_start, afternoon_end = _briefing_window(
        date(2026, 4, 22), BRIEFING_TYPE_AFTERNOON, "Asia/Seoul"
    )

    assert morning_start.isoformat() == "2026-04-21T06:30:00+00:00"
    assert morning_end.isoformat() == "2026-04-21T22:20:00+00:00"
    assert afternoon_start.isoformat() == "2026-04-21T22:30:00+00:00"
    assert afternoon_end.isoformat() == "2026-04-22T07:20:00+00:00"


def test_sanitize_payload_replaces_untranslated_titles() -> None:
    item = _news_item(
        20,
        "dev",
        "4 JavaScript Frameworks Powering the Generative AI Revolution",
        "Dev.to",
        excerpt="A guide to JavaScript frameworks for generative AI apps.",
    )
    grouped = {"dev": [item], "investment": [], "ai": []}
    payload = {
        "title": "2026년 4월 22일 아침 브리핑",
        "one_liner": "4 JavaScript Frameworks Powering the Generative AI Revolution 주목",
        "keywords": ["JavaScript", "AI"],
        "sections": {
            "dev": {
                "summary": "4 JavaScript Frameworks Powering the Generative AI Revolution 이슈가 중심입니다.",
                "highlights": [
                    {
                        "news_id": 20,
                        "title": item.title,
                        "title_ko": item.title,
                        "url": item.url,
                        "source": item.source_name,
                        "reason": "A guide to JavaScript frameworks for generative AI apps.",
                        "summary": "A guide to JavaScript frameworks for generative AI apps.",
                    }
                ],
            },
            "investment": {"summary": "", "highlights": []},
            "ai": {"summary": "", "highlights": []},
        },
    }

    sanitized = _sanitize_payload(
        payload, grouped, date(2026, 4, 22), BRIEFING_TYPE_MORNING
    )

    assert item.title not in sanitized["one_liner"]
    assert item.title not in sanitized["sections"]["dev"]["summary"]
    assert (
        sanitized["sections"]["dev"]["highlights"][0]["title_ko"]
        == "JavaScript·프레임워크 관련 해외 기사"
    )
    assert (
        "JavaScript frameworks"
        not in sanitized["sections"]["dev"]["highlights"][0]["reason"]
    )
    assert sanitized["sections"]["dev"]["highlights"][0]["summary"]


def test_article_ranking_uses_relevance_and_source_diversity() -> None:
    items = [
        _news_item(10, "investment", "일반 증시 뉴스", "MarketWatch", hours_ago=1),
        _news_item(
            11,
            "investment",
            "FOMC 금리 환율 반도체 수출 ETF 동향",
            "MarketWatch",
            hours_ago=6,
        ),
        _news_item(
            12, "investment", "금리 인하 기대와 유가 변동", "MarketWatch", hours_ago=7
        ),
        _news_item(
            13,
            "investment",
            "코스피 실적 반도체 투자 심리 개선",
            "매일경제 금융",
            hours_ago=8,
        ),
        _news_item(
            14,
            "investment",
            "나스닥 ETF 반등",
            "Investing.com Stock Market News",
            hours_ago=9,
        ),
    ]

    grouped = _group_ranked_news(items, datetime.now())
    investment_titles = [item.title for item in grouped["investment"]]

    assert investment_titles[0] == "FOMC 금리 환율 반도체 수출 ETF 동향"
    assert "일반 증시 뉴스" not in investment_titles[:3]
    assert sum(item.source_name == "MarketWatch" for item in grouped["investment"]) == 2


def test_fallback_payload_limits_highlights_to_three_items_per_section() -> None:
    sources = [
        "OpenAI News",
        "Google DeepMind News",
        "NVIDIA Blog",
        "OpenAI News",
        "MIT News AI",
    ]
    items = [
        _news_item(
            news_id,
            "ai",
            f"AI 기사 {news_id}",
            source_name,
            excerpt=f"요약 {news_id}.",
        )
        for news_id, source_name in zip(range(30, 35), sources, strict=True)
    ]

    grouped = _group_ranked_news(items, datetime.now())
    payload = _build_fallback_payload(grouped, date(2026, 4, 23))

    assert len(payload["sections"]["ai"]["highlights"]) == 3


def test_sparse_categories_are_marked_for_recent_backfill() -> None:
    grouped = {
        "dev": [
            _news_item(1, "dev", "개발 기사 1", "GitHub Blog"),
            _news_item(2, "dev", "개발 기사 2", "AWS News Blog"),
            _news_item(3, "dev", "개발 기사 3", "React Status"),
        ],
        "investment": [
            _news_item(4, "investment", "투자 기사 1", "연합뉴스 경제"),
            _news_item(5, "investment", "투자 기사 2", "한국경제 증권"),
            _news_item(6, "investment", "투자 기사 3", "CNBC Markets"),
        ],
        "ai": [_news_item(7, "ai", "AI 기사 1", "OpenAI News")],
    }

    assert _categories_needing_backfill(grouped) == ["ai"]


def test_prompt_articles_prefers_article_body_over_rss_excerpt() -> None:
    grouped = {
        "dev": [
            _news_item_with_article_text(
                10,
                "dev",
                "AI 에이전트 프레임워크 업데이트",
                "GitHub Blog",
                "원문 본문 첫 문장입니다. 원문 본문 두 번째 문장입니다. 원문 본문 세 번째 문장입니다.",
            )
        ],
        "investment": [],
        "ai": [],
    }

    prompt = _prompt_articles(grouped)

    assert "article_text" in prompt
    assert "원문 본문 첫 문장입니다." in prompt


def test_article_based_highlight_summary_uses_cached_article_text() -> None:
    item = _news_item_with_article_text(
        20,
        "ai",
        "AI 인프라 기사",
        "NVIDIA Blog",
        "첫 문장입니다. 둘째 문장입니다. 셋째 문장입니다. 넷째 문장입니다.",
    )

    summary = _article_based_highlight_summary(item)

    assert "첫 문장입니다." in summary
    assert "둘째 문장입니다." in summary
