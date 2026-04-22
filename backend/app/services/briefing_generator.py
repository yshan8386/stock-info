from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from html import unescape
from typing import Any
from zoneinfo import ZoneInfo

from anthropic import Anthropic
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Briefing, News

BRIEFING_CATEGORIES = ("dev", "investment", "ai")
SECTION_LABELS = {"dev": "개발/기술", "investment": "투자/금융", "ai": "AI/ML"}
PROMPT_ARTICLES_PER_CATEGORY = 3
CLAUDE_MAX_TOKENS = 900
logger = logging.getLogger(__name__)
HTML_PATTERN = re.compile(r"<[^>]+>")
MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[[^\]]*]\([^)]*\)")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)]\([^)]*\)")
WHITESPACE_PATTERN = re.compile(r"\s+")
HANGUL_PATTERN = re.compile(r"[가-힣]")
ASCII_WORD_PATTERN = re.compile(r"[A-Za-z]{3,}")
MAX_REASON_LENGTH = 180

BRIEFING_TYPE_MORNING = "daily_morning"
BRIEFING_TYPE_AFTERNOON = "daily_afternoon"
BRIEFING_TYPE_LABELS = {
    BRIEFING_TYPE_MORNING: "아침",
    BRIEFING_TYPE_AFTERNOON: "오후",
}

BRIEFING_WINDOWS = {
    BRIEFING_TYPE_MORNING: {
        "start_offset_days": -1,
        "start_hour": 15,
        "start_minute": 30,
        "end_offset_days": 0,
        "end_hour": 7,
        "end_minute": 20,
    },
    BRIEFING_TYPE_AFTERNOON: {
        "start_offset_days": 0,
        "start_hour": 7,
        "start_minute": 30,
        "end_offset_days": 0,
        "end_hour": 16,
        "end_minute": 20,
    },
}

TITLE_HINTS = {
    "javascript": "JavaScript",
    "framework": "프레임워크",
    "docker": "Docker",
    "react": "React",
    "python": "Python",
    "security": "보안",
    "performance": "성능",
    "agent": "AI 에이전트",
    "generative ai": "생성형 AI",
    "openai": "OpenAI",
    "claude": "Claude",
    "model": "AI 모델",
    "nvidia": "NVIDIA",
    "earnings": "실적",
    "etf": "ETF",
    "stock": "증시",
}

CATEGORY_KEYWORDS = {
    "dev": {
        "react": 7,
        "next.js": 7,
        "typescript": 6,
        "python": 5,
        "postgres": 5,
        "docker": 4,
        "kubernetes": 4,
        "security": 5,
        "performance": 4,
        "보안": 5,
        "성능": 4,
        "프론트엔드": 4,
        "백엔드": 4,
    },
    "investment": {
        "금리": 9,
        "환율": 8,
        "반도체": 8,
        "수출": 7,
        "실적": 7,
        "fomc": 8,
        "etf": 6,
        "코스피": 6,
        "나스닥": 6,
        "유가": 7,
        "인플레이션": 7,
        "관세": 6,
        "fed": 7,
        "treasury": 5,
        "earnings": 6,
    },
    "ai": {
        "claude": 9,
        "openai": 9,
        "gemini": 8,
        "llm": 7,
        "agent": 7,
        "model": 5,
        "gpu": 7,
        "nvidia": 8,
        "anthropic": 8,
        "ai 에이전트": 7,
        "인공지능": 6,
        "모델": 5,
    },
}

SOURCE_WEIGHTS = {
    "GeekNews": 4,
    "Hacker News": 3,
    "React Status": 4,
    "JavaScript Weekly": 3,
    "OpenAI Blog": 6,
    "Hugging Face Blog": 5,
    "Google AI Blog": 5,
    "매일경제 금융": 5,
    "Google News 국내 증시": 4,
    "Investing.com Stock Market News": 4,
    "MarketWatch Top Stories": 4,
    "The Motley Fool": 3,
}


def _section_label(category: str) -> str:
    return SECTION_LABELS.get(category, category)


def _normalize_title(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    normalized = re.sub(r"[^0-9a-zA-Z가-힣 ]+", "", normalized)
    return normalized


def _clean_text(value: str | None, max_length: int = MAX_REASON_LENGTH) -> str:
    if not value:
        return ""
    text = MARKDOWN_IMAGE_PATTERN.sub(" ", value)
    text = MARKDOWN_LINK_PATTERN.sub(r"\1", text)
    text = unescape(HTML_PATTERN.sub(" ", text))
    text = re.sub(r"(^|\s)>+\s*", " ", text)
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text


def _has_meaningful_korean(value: str | None) -> bool:
    return len(HANGUL_PATTERN.findall(value or "")) >= 2


def _looks_untranslated(value: str | None) -> bool:
    text = value or ""
    return bool(ASCII_WORD_PATTERN.search(text)) and not _has_meaningful_korean(text)


def _fallback_korean_title(item: News) -> str:
    if _has_meaningful_korean(item.title):
        return item.title
    lowered = item.title.lower()
    hints = []
    for keyword, label in TITLE_HINTS.items():
        if keyword in lowered and label not in hints:
            hints.append(label)
        if len(hints) >= 2:
            break
    if hints:
        return f"{'·'.join(hints)} 관련 해외 기사"
    return f"{_section_label(item.category)} 주요 해외 기사"


def _coerce_korean_title(item: News, value: str | None) -> str:
    candidate = _clean_text(value, 120)
    if candidate and "주요 해외 기사" not in candidate and not _looks_untranslated(candidate):
        return candidate
    return _fallback_korean_title(item)


def _fallback_reason(item: News) -> str:
    excerpt = _clean_text(item.content_excerpt)
    if excerpt and not _looks_untranslated(excerpt):
        return excerpt
    return f"{item.source_name}에서 확인된 {_section_label(item.category)} 관련 주요 기사입니다."


def _replace_raw_titles(value: str | None, items: list[News], max_length: int = MAX_REASON_LENGTH) -> str:
    text = _clean_text(value, max_length * 3)
    for item in items:
        raw_title = item.title.strip()
        if len(raw_title) >= 8:
            text = text.replace(raw_title, _fallback_korean_title(item))
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _article_score(item: News, now: datetime) -> tuple[float, float]:
    published_at = item.published_at or item.collected_at or now
    normalized_now = _as_utc(now)
    normalized_published_at = _as_utc(published_at)
    hours_old = max((normalized_now - normalized_published_at).total_seconds() / 3600, 0)
    freshness = max(0.0, 36 - hours_old) * 0.35
    title_bonus = min(len(item.title.split()), 12) * 0.4
    excerpt_bonus = 1.5 if item.content_excerpt else 0
    source_bonus = SOURCE_WEIGHTS.get(item.source_name, 0)
    keyword_bonus = _keyword_score(item)
    return freshness + title_bonus + excerpt_bonus + source_bonus + keyword_bonus, normalized_published_at.timestamp()


def _keyword_score(item: News) -> float:
    text = f"{item.title} {_clean_text(item.content_excerpt, 400)}".lower()
    weights = CATEGORY_KEYWORDS.get(item.category, {})
    return float(sum(weight for keyword, weight in weights.items() if keyword.lower() in text))


def _group_ranked_news(news_items: list[News], now: datetime) -> dict[str, list[News]]:
    grouped: dict[str, list[News]] = {category: [] for category in BRIEFING_CATEGORIES}
    seen_titles: set[tuple[str, str]] = set()
    seen_urls: set[str] = set()
    source_counts: dict[tuple[str, str], int] = {}

    for item in sorted(news_items, key=lambda news: _article_score(news, now), reverse=True):
        if item.category not in grouped:
            continue
        normalized_title = _normalize_title(item.title)
        dedupe_key = (item.category, normalized_title)
        if item.url in seen_urls or dedupe_key in seen_titles:
            continue
        source_key = (item.category, item.source_name)
        if source_counts.get(source_key, 0) >= 2:
            continue
        seen_urls.add(item.url)
        seen_titles.add(dedupe_key)
        source_counts[source_key] = source_counts.get(source_key, 0) + 1
        grouped[item.category].append(item)

    return grouped


def _pick_highlights(grouped_news: dict[str, list[News]], per_category: int = 3) -> dict[str, list[News]]:
    return {category: items[:per_category] for category, items in grouped_news.items()}


def _extract_keywords(items: list[News]) -> list[str]:
    keywords: list[str] = []
    seen: set[str] = set()
    for item in items:
        candidates = [part.strip("[]()\"'.,:") for part in re.split(r"\s+", item.title) if len(part.strip()) >= 2]
        for candidate in candidates:
            lowered = candidate.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            keywords.append(candidate)
            break
        if len(keywords) >= 8:
            break
    return keywords


def _build_fallback_section(category: str, items: list[News]) -> dict[str, Any]:
    label = _section_label(category)
    if not items:
        return {
            "label": label,
            "summary": f"{label} 섹션은 아직 선별된 기사가 없어 다음 수집 주기를 기다리고 있습니다.",
            "highlights": [],
        }

    sources = ", ".join(dict.fromkeys(item.source_name for item in items[:3]))
    headline = ", ".join(_fallback_korean_title(item) for item in items[:2])
    return {
        "label": label,
        "summary": f"{label} 섹션에서는 {headline} 이슈가 중심입니다. 주요 출처는 {sources}입니다.",
        "highlights": [
            {
                "news_id": item.id,
                "title": item.title,
                "title_ko": _fallback_korean_title(item),
                "url": item.url,
                "source": item.source_name,
                "reason": _fallback_reason(item),
            }
            for item in items
        ],
    }


def _briefing_type_label(briefing_type: str) -> str:
    return BRIEFING_TYPE_LABELS.get(briefing_type, "데일리")


def _briefing_window(target_date: date, briefing_type: str, timezone_name: str) -> tuple[datetime, datetime]:
    if briefing_type not in BRIEFING_WINDOWS:
        raise ValueError(f"Unsupported briefing_type: {briefing_type}")

    tz = ZoneInfo(timezone_name)
    window = BRIEFING_WINDOWS[briefing_type]
    start_date = target_date + timedelta(days=window["start_offset_days"])
    end_date = target_date + timedelta(days=window["end_offset_days"])
    start = datetime(
        start_date.year,
        start_date.month,
        start_date.day,
        window["start_hour"],
        window["start_minute"],
        tzinfo=tz,
    )
    end = datetime(
        end_date.year,
        end_date.month,
        end_date.day,
        window["end_hour"],
        window["end_minute"],
        tzinfo=tz,
    )
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def _build_fallback_payload(grouped_news: dict[str, list[News]], target_date: date, briefing_type: str = BRIEFING_TYPE_MORNING) -> dict[str, Any]:
    highlights = _pick_highlights(grouped_news)
    all_items = [item for category in BRIEFING_CATEGORIES for item in highlights[category]]
    label = _briefing_type_label(briefing_type)
    top_titles = [_fallback_korean_title(item) for item in all_items[:3]]
    one_liner = (
        " / ".join(top_titles[:2]) + " 흐름을 중심으로 시장과 기술 이슈를 정리했습니다."
        if top_titles
        else "수집된 RSS 기사를 바탕으로 오늘 확인할 이슈를 정리했습니다."
    )

    sections = {category: _build_fallback_section(category, highlights[category]) for category in BRIEFING_CATEGORIES}
    return {
        "title": f"{target_date.isoformat()} {label} 브리핑",
        "one_liner": one_liner[:120],
        "keywords": _extract_keywords(all_items),
        "sections": sections,
    }


def _prompt_articles(grouped_news: dict[str, list[News]]) -> str:
    payload: dict[str, list[dict[str, Any]]] = {}
    for category in BRIEFING_CATEGORIES:
        payload[category] = [
            {
                "news_id": item.id,
                "title": item.title,
                "url": item.url,
                "source": item.source_name,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "excerpt": _clean_text(item.content_excerpt, 260),
            }
            for item in grouped_news[category][:PROMPT_ARTICLES_PER_CATEGORY]
        ]
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _strip_json_block(value: str) -> str:
    content = value.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content).strip()
        content = re.sub(r"```$", "", content).strip()
    return content


def _call_claude_for_briefing(grouped_news: dict[str, list[News]], target_date: date, briefing_type: str) -> dict[str, Any]:
    settings = get_settings()
    if settings.mock_claude or not settings.anthropic_api_key:
        raise RuntimeError("Claude generation disabled")

    label = _briefing_type_label(briefing_type)
    prompt = f"""
날짜: {target_date.isoformat()}
브리핑 종류: {label}

아래 기사 후보를 참고해서 build_daily_briefing 도구를 호출하세요.
- title, one_liner, summary, title_ko, reason은 모두 한국어로 작성하세요.
- 외국어 기사 제목을 summary/reason에 그대로 복사하지 말고 한국어 의미로 풀어서 쓰세요.
- 제품명, 회사명, 기술명은 원어 표기를 유지해도 되지만 문장 자체는 한국어여야 합니다.
- one_liner: 55자 이내
- keywords: 5~8개
- sections.dev/investment/ai 각각 summary 2문장 이내
- highlights는 카테고리별 최대 2개
- highlights 항목은 news_id, title, title_ko, url, source, reason 포함
- title_ko는 외국어 제목이면 자연스러운 한국어 제목으로 번역하고, 한국어 제목이면 그대로 사용
- reason은 1문장, 60자 이내
- 입력 기사에 없는 사실을 만들지 마세요

기사 후보:
{_prompt_articles(grouped_news)}
""".strip()

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=CLAUDE_MAX_TOKENS,
        temperature=0,
        system="당신은 개인 투자자를 위한 한국어 브리핑 편집자입니다. 반드시 제공된 도구만 호출하고, 사용자에게 보이는 문장은 한국어로 작성합니다.",
        messages=[{"role": "user", "content": prompt}],
        tools=[
            {
                "name": "build_daily_briefing",
                "description": "Build a structured daily briefing from selected RSS articles.",
                "input_schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title", "one_liner", "keywords", "sections"],
                    "properties": {
                        "title": {"type": "string"},
                        "one_liner": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
                        "sections": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["dev", "investment", "ai"],
                            "properties": {
                                category: {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["summary", "highlights"],
                                    "properties": {
                                        "summary": {"type": "string"},
                                        "highlights": {
                                            "type": "array",
                                            "maxItems": 2,
                                            "items": {
                                                "type": "object",
                                                "additionalProperties": False,
                                                "required": ["news_id", "title", "title_ko", "url", "source", "reason"],
                                                "properties": {
                                                    "news_id": {"type": "integer"},
                                                    "title": {"type": "string"},
                                                    "title_ko": {"type": "string"},
                                                    "url": {"type": "string"},
                                                    "source": {"type": "string"},
                                                    "reason": {"type": "string"},
                                                },
                                            },
                                        },
                                    },
                                }
                                for category in BRIEFING_CATEGORIES
                            },
                        },
                    },
                },
            }
        ],
        tool_choice={"type": "tool", "name": "build_daily_briefing"},
    )

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "build_daily_briefing":
            return dict(block.input)
    raise RuntimeError("Claude returned no build_daily_briefing tool call")


def _sanitize_payload(payload: dict[str, Any], grouped_news: dict[str, list[News]], target_date: date, briefing_type: str) -> dict[str, Any]:
    fallback = _build_fallback_payload(grouped_news, target_date, briefing_type)
    result = {
        "title": str(payload.get("title") or fallback["title"]),
        "one_liner": str(payload.get("one_liner") or fallback["one_liner"])[:120],
        "keywords": payload.get("keywords") or fallback["keywords"],
        "sections": {},
    }

    known_by_id = {item.id: item for items in grouped_news.values() for item in items}
    all_known_items = [item for items in grouped_news.values() for item in items]
    result["one_liner"] = _replace_raw_titles(result["one_liner"], all_known_items, 120) or fallback["one_liner"]
    for category in BRIEFING_CATEGORIES:
        incoming = payload.get("sections", {}).get(category, {})
        fallback_section = fallback["sections"][category]
        category_items = grouped_news.get(category, [])
        highlights: list[dict[str, Any]] = []
        for item in incoming.get("highlights", []):
            news_id = item.get("news_id")
            source_item = known_by_id.get(news_id)
            if source_item is None:
                continue
            reason = _replace_raw_titles(str(item.get("reason") or ""), [source_item], 80)
            if not reason or _looks_untranslated(reason):
                reason = _fallback_reason(source_item)
            highlights.append(
                {
                    "news_id": source_item.id,
                    "title": source_item.title,
                    "title_ko": _coerce_korean_title(source_item, str(item.get("title_ko") or "")),
                    "url": source_item.url,
                    "source": source_item.source_name,
                    "reason": reason,
                }
            )
        if not highlights:
            highlights = fallback_section["highlights"]

        summary = _replace_raw_titles(str(incoming.get("summary") or ""), category_items, 260)
        if not summary or "주요 해외 기사" in summary or _looks_untranslated(summary):
            summary = fallback_section["summary"]
        result["sections"][category] = {
            "label": fallback_section["label"],
            "summary": summary,
            "highlights": highlights,
        }

    if not isinstance(result["keywords"], list):
        result["keywords"] = fallback["keywords"]
    result["keywords"] = [str(keyword).strip() for keyword in result["keywords"] if str(keyword).strip()][:8]
    return result


def _render_markdown(payload: dict[str, Any], target_date: date, briefing_type: str = BRIEFING_TYPE_MORNING) -> str:
    label = _briefing_type_label(briefing_type)
    lines = [
        f"# {target_date.strftime('%Y년 %-m월 %-d일')} {label} 브리핑",
        "",
        "## 한 줄 요약",
        payload["one_liner"],
        "",
    ]

    for category in BRIEFING_CATEGORIES:
        section = payload["sections"][category]
        lines.append(f"## {section['label']}")
        lines.append(section["summary"])
        lines.append("")
        lines.append("**주목할 기사**")
        if section["highlights"]:
            for highlight in section["highlights"]:
                title = highlight.get("title_ko") or highlight["title"]
                lines.append(f"- [{title}]({highlight['url']}): {highlight['reason']}")
        else:
            lines.append("- 아직 선별된 기사가 없습니다.")
        lines.append("")

    lines.append("## 오늘의 키워드")
    lines.append(", ".join(payload["keywords"]) or "데이터 수집 대기")
    return "\n".join(lines)


def generate_daily_briefing(
    db: Session,
    target_date: date | None = None,
    briefing_type: str = BRIEFING_TYPE_MORNING,
) -> Briefing:
    settings = get_settings()
    local_now = datetime.now(ZoneInfo(settings.timezone))
    target_date = target_date or local_now.date()
    window_start, window_end = _briefing_window(target_date, briefing_type, settings.timezone)
    now = datetime.now(timezone.utc)
    news_items = list(
        db.scalars(
            select(News)
            .where(
                News.published_at >= window_start,
                News.published_at < window_end,
                News.content_excerpt.is_not(None),
                func.length(func.trim(News.content_excerpt)) > 0,
            )
            .order_by(desc(News.published_at), desc(News.id))
        ).all()
    )
    grouped_news = _group_ranked_news(news_items, now)

    model_used = "fallback_rule_based"
    try:
        payload = _sanitize_payload(
            _call_claude_for_briefing(grouped_news, target_date, briefing_type),
            grouped_news,
            target_date,
            briefing_type,
        )
        model_used = settings.claude_model
    except Exception as exc:
        logger.warning("Claude briefing generation failed; using fallback", exc_info=exc)
        payload = _build_fallback_payload(grouped_news, target_date, briefing_type)

    markdown = _render_markdown(payload, target_date, briefing_type)
    highlighted_news_ids = [
        highlight["news_id"]
        for category in BRIEFING_CATEGORIES
        for highlight in payload["sections"][category]["highlights"]
    ]

    briefing = db.scalar(
        select(Briefing).where(
            Briefing.briefing_date == target_date,
            Briefing.briefing_type == briefing_type,
        )
    )
    if briefing is None:
        briefing = Briefing(briefing_date=target_date, briefing_type=briefing_type, content_markdown=markdown)
        db.add(briefing)

    briefing.title = payload["title"]
    briefing.one_liner = payload["one_liner"]
    briefing.content_markdown = markdown
    briefing.content_sections = payload["sections"]
    briefing.highlighted_news_ids = highlighted_news_ids
    briefing.keywords = payload["keywords"]
    briefing.source_article_count = len(news_items)
    briefing.model_used = model_used
    briefing.generated_at = now
    db.commit()
    db.refresh(briefing)
    return briefing
