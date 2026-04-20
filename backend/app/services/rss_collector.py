from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import News, RssFeed

USER_AGENT = "ysj.brief feed validator"


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


async def fetch_feed(feed: RssFeed) -> tuple[str, list[dict], str | None]:
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
    for entry in parsed.entries[:50]:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue
        entries.append(
            {
                "title": title,
                "url": link,
                "author": entry.get("author"),
                "published_at": _parse_datetime(entry.get("published")),
                "content_excerpt": entry.get("summary"),
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
        feed.last_fetched_at = datetime.now()
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

