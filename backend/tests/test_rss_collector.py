from app.services.rss_collector import clean_feed_excerpt, clean_feed_title


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
