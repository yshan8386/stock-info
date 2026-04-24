from datetime import datetime

from app.models import News
from app.services.article_extractor import (
    cache_article_fetch_result,
    extract_article_text_from_html,
    get_cached_article_text,
    should_retry_article_fetch,
)


def _news(raw_data: dict | None = None) -> News:
    return News(
        id=1,
        title="테스트 기사",
        url="https://example.com/article",
        source_feed_id=None,
        source_name="테스트 소스",
        category="ai",
        author=None,
        published_at=datetime.now(),
        content_excerpt="짧은 RSS 요약",
        raw_data=raw_data,
        collected_at=datetime.now(),
    )


def test_extract_article_text_from_html_prefers_main_article_content() -> None:
    html = """
    <html>
      <body>
        <header><p>navigation</p></header>
        <article>
          <p>첫 번째 문단입니다. 이 문단은 기사 핵심을 설명합니다.</p>
          <p>두 번째 문단입니다. 왜 중요한지까지 이어서 설명합니다.</p>
          <p>세 번째 문단입니다. 실무자나 투자자가 볼 지점을 정리합니다.</p>
        </article>
        <footer><p>copyright</p></footer>
      </body>
    </html>
    """

    article_text = extract_article_text_from_html(html)

    assert article_text is not None
    assert "첫 번째 문단입니다." in article_text
    assert "세 번째 문단입니다." in article_text
    assert "navigation" not in article_text


def test_cached_article_text_is_reused_after_successful_fetch() -> None:
    item = _news()

    cache_article_fetch_result(item, "원문 본문 첫 문장. 원문 본문 둘째 문장.")

    assert get_cached_article_text(item) == "원문 본문 첫 문장. 원문 본문 둘째 문장."
    assert should_retry_article_fetch(item) is False
