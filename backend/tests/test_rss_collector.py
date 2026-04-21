import asyncio
from datetime import UTC, datetime, timedelta

from app.models import RssFeed
from app.services import rss_collector
from app.services.rss_collector import clean_feed_excerpt, clean_feed_title, is_recent_entry


def test_clean_feed_excerpt_removes_html_and_limits_length() -> None:
    raw = """
    <table><tr><td><img src="x.png" /></td></tr></table>
    <p>React 19 release details &amp; migration notes.</p>
    <a href="https://example.com">Read more</a>
    """

    cleaned = clean_feed_excerpt(raw, max_length=40)

    assert cleaned is not None
    assert cleaned.startswith("React 19 release details & migration")
    assert len(cleaned) <= 43
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "href" not in cleaned


def test_clean_feed_title_removes_geeknews_prefix() -> None:
    assert clean_feed_title("Show GN: 새 도구 공개") == "새 도구 공개"


def test_is_recent_entry_requires_published_at_within_one_hour() -> None:
    now = datetime(2026, 4, 22, 9, 0, tzinfo=UTC)

    assert is_recent_entry(now - timedelta(minutes=59), now)
    assert not is_recent_entry(now - timedelta(hours=1, seconds=1), now)
    assert not is_recent_entry(now + timedelta(seconds=1), now)
    assert not is_recent_entry(None, now)


def test_fetch_feed_keeps_only_recent_entries_with_excerpt(monkeypatch) -> None:
    now = datetime(2026, 4, 22, 9, 0, tzinfo=UTC)
    rss = """
    <rss version="2.0">
      <channel>
        <item>
          <title>제목만 있는 기사</title>
          <link>https://example.com/no-summary</link>
          <pubDate>Wed, 22 Apr 2026 08:30:00 GMT</pubDate>
        </item>
        <item>
          <title>오래된 기사</title>
          <link>https://example.com/old-summary</link>
          <pubDate>Wed, 22 Apr 2026 07:30:00 GMT</pubDate>
          <description><![CDATA[<p>오래된 요약입니다.</p>]]></description>
        </item>
        <item>
          <title>본문이 있는 기사</title>
          <link>https://example.com/with-summary</link>
          <pubDate>Wed, 22 Apr 2026 08:30:00 GMT</pubDate>
          <description><![CDATA[<p>요약 본문입니다.</p>]]></description>
        </item>
      </channel>
    </rss>
    """

    class DummyResponse:
        text = rss

        def raise_for_status(self) -> None:
            return None

    class DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> DummyResponse:
            return DummyResponse()

    monkeypatch.setattr(rss_collector.httpx, "AsyncClient", DummyClient)

    feed = RssFeed(id=1, name="테스트", url="https://example.com/rss", category="dev", language="ko")
    status, entries, error = asyncio.run(rss_collector.fetch_feed(feed, now=now))

    assert status == "success"
    assert error is None
    assert len(entries) == 1
    assert entries[0]["url"] == "https://example.com/with-summary"
    assert entries[0]["content_excerpt"] == "요약 본문입니다."
