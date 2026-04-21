from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
import re

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import News, RssFeed

USER_AGENT = "ysj.brief feed validator"
RECENT_ENTRY_WINDOW = timedelta(hours=1)
TITLE_PREFIX_PATTERN = re.compile(r"^(Show|Ask|Tell)\s+GN:\s*", re.IGNORECASE)
HTML_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def is_recent_entry(published_at: datetime | None, now: datetime, window: timedelta = RECENT_ENTRY_WINDOW) -> bool:
    if published_at is None:
        return False
    normalized_now = now.astimezone(UTC) if now.tzinfo else now.replace(tzinfo=UTC)
    normalized_published_at = published_at.astimezone(UTC) if published_at.tzinfo else published_at.replace(tzinfo=UTC)
    return normalized_now - window <= normalized_published_at <= normalized_now


def clean_feed_title(title: str) -> str:
    return TITLE_PREFIX_PATTERN.sub("", title).strip()


def clean_feed_excerpt(value: str | None, max_length: int = 400) -> str | None:
    if not value:
        return None
    text = unescape(HTML_PATTERN.sub(" ", value))
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    if not text:
        return None
    return text[:max_length].rstrip() + ("..." if len(text) > max_length else "")


async def fetch_feed(feed: RssFeed, now: datetime | None = None) -> tuple[str, list[dict], str | None]:
    try:
        async with httpx.AsyncClient(timeout=10, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            response = await client.get(feed.url)
            response.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        return "failed", [], str(exc)

    parsed = feedparser.parse(response.text)
    if parsed.bozo and not parsed.entries:
        return "failed", [], str(parsed.bozo_exception)
    entries = []
    fetched_at = now or datetime.now(UTC)
    for entry in parsed.entries[:50]:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue
        published_at = _parse_datetime(entry.get("published"))
        if not is_recent_entry(published_at, fetched_at):
            continue
        excerpt = (
            clean_feed_excerpt(entry.get("summary"))
            or clean_feed_excerpt(entry.get("description"))
            or clean_feed_excerpt(entry.get("content", [{}])[0].get("value") if entry.get("content") else None)
        )
        if not excerpt:
            continue
        entries.append(
            {
                "title": clean_feed_title(title),
                "url": link,
                "author": entry.get("author"),
                "published_at": published_at,
                "content_excerpt": excerpt,
                "raw_data": {
                    "id": entry.get("id"),
                    "published": entry.get("published"),
                    "tags": [tag.get("term") for tag in entry.get("tags", [])],
                },
            }
        )
    return "success", entries, None


async def collect_all_feeds(db: Session) -> dict[str, int]:
    feeds = list(db.scalars(select(RssFeed).where(RssFeed.is_active.is_(True))))
    inserted = 0
    failed = 0
    for feed in feeds:
        status, entries, error = await fetch_feed(feed)
        feed.last_fetched_at = datetime.now(UTC)
        feed.last_fetched_status = status
        feed.last_error = error
        if status != "success":
            failed += 1
            continue
        for entry in entries:
            exists = db.scalar(select(News.id).where(News.url == entry["url"]))
            if exists:
                continue
            db.add(
                News(
                    title=entry["title"],
                    url=entry["url"],
                    source_feed_id=feed.id,
                    source_name=feed.name,
                    category=feed.category,
                    author=entry["author"],
                    published_at=entry["published_at"],
                    content_excerpt=entry["content_excerpt"],
                    raw_data=entry["raw_data"],
                )
            )
            inserted += 1
    db.commit()
    return {"feeds": len(feeds), "inserted": inserted, "failed": failed}
