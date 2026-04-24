from __future__ import annotations

from datetime import UTC, datetime, timedelta
from html import unescape
import re
from typing import Any

from bs4 import BeautifulSoup
import httpx
from sqlalchemy.orm import Session

from app.models import News

USER_AGENT = "ysj.brief article extractor"
ARTICLE_TIMEOUT_SECONDS = 8
ARTICLE_MAX_LENGTH = 4000
ARTICLE_CACHE_RETRY_WINDOW = timedelta(hours=12)
WHITESPACE_PATTERN = re.compile(r"\s+")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
BOILERPLATE_PATTERNS = (
    "javascript is required",
    "all rights reserved",
    "subscribe to continue",
    "sign up for",
    "cookie policy",
    "privacy policy",
    "advertisement",
)
ARTICLE_SELECTORS = (
    "article",
    "main",
    "[role='main']",
    ".article-body",
    ".article__body",
    ".article-body__content",
    ".entry-content",
    ".post-content",
    ".story-body",
    ".story-content",
    "#content",
)


def _clean_text(value: str | None, max_length: int = ARTICLE_MAX_LENGTH) -> str:
    if not value:
        return ""
    text = unescape(HTML_COMMENT_PATTERN.sub(" ", value))
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    if len(text) > max_length:
        return text[:max_length].rstrip() + "..."
    return text


def _normalize_paragraphs(paragraphs: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for paragraph in paragraphs:
        text = _clean_text(paragraph, 700)
        lowered = text.lower()
        if len(text) < 20:
            continue
        if any(pattern in lowered for pattern in BOILERPLATE_PATTERNS):
            continue
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
    return normalized


def extract_article_text_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(
        ["script", "style", "noscript", "svg", "form", "header", "footer"]
    ):
        node.decompose()

    candidates = [soup.select_one(selector) for selector in ARTICLE_SELECTORS]
    containers = [candidate for candidate in candidates if candidate is not None]
    if not containers:
        containers = [soup.body or soup]

    best_text = ""
    for container in containers:
        paragraphs = [
            element.get_text(" ", strip=True)
            for element in container.find_all(["p", "h2", "h3", "li"])
        ]
        normalized = _normalize_paragraphs(paragraphs)
        article_text = "\n".join(normalized)
        if len(article_text) > len(best_text):
            best_text = article_text

    cleaned = _clean_text(best_text)
    return cleaned or None


def _raw_data(item: News) -> dict[str, Any]:
    return dict(item.raw_data or {})


def get_cached_article_text(item: News) -> str | None:
    cached = _clean_text(_raw_data(item).get("article_text"))
    return cached or None


def should_retry_article_fetch(item: News, now: datetime | None = None) -> bool:
    raw_data = _raw_data(item)
    if get_cached_article_text(item):
        return False
    attempted_at = raw_data.get("article_fetch_attempted_at")
    if not attempted_at:
        return True
    try:
        attempted = datetime.fromisoformat(str(attempted_at))
    except ValueError:
        return True
    current = now or datetime.now(UTC)
    return current - attempted.astimezone(UTC) >= ARTICLE_CACHE_RETRY_WINDOW


def cache_article_fetch_result(
    item: News, article_text: str | None, error: str | None = None
) -> None:
    payload = _raw_data(item)
    payload["article_fetch_attempted_at"] = datetime.now(UTC).isoformat()
    payload["article_fetch_error"] = error
    if article_text:
        payload["article_text"] = article_text
        payload["article_fetched_at"] = payload["article_fetch_attempted_at"]
    item.raw_data = payload


def fetch_article_text(url: str, client: httpx.Client) -> str | None:
    response = client.get(
        url,
        timeout=ARTICLE_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )
    response.raise_for_status()
    return extract_article_text_from_html(response.text)


def enrich_news_with_article_text(db: Session, items: list[News]) -> None:
    pending = [item for item in items if should_retry_article_fetch(item)]
    if not pending:
        return

    with httpx.Client() as client:
        for item in pending:
            try:
                article_text = fetch_article_text(item.url, client)
                cache_article_fetch_result(item, article_text)
            except Exception as exc:  # noqa: BLE001
                cache_article_fetch_result(item, None, str(exc))
            db.add(item)
