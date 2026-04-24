import asyncio

import feedparser
import httpx

FEEDS = [
    "https://news.hada.io/rss/news",
    "https://toss.tech/rss.xml",
    "https://tech.kakao.com/feed/",
    "https://meetup.nhncloud.com/rss",
    "https://github.blog/feed/",
    "https://aws.amazon.com/blogs/aws/feed/",
    "https://devblogs.microsoft.com/feed/",
    "https://react.statuscode.com/rss",
    "https://javascriptweekly.com/rss",
    "https://www.mk.co.kr/rss/30100041/",
    "https://www.hankyung.com/feed/finance",
    "https://www.hankyung.com/feed/economy",
    "https://www.yna.co.kr/rss/economy.xml",
    "https://www.asiae.co.kr/rss/stock.htm",
    "https://news.google.com/rss/search?q=%EB%B0%98%EB%8F%84%EC%B2%B4%20%EC%8B%A4%EC%A0%81%20%EC%88%98%EC%B6%9C%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=2%EC%B0%A8%EC%A0%84%EC%A7%80%20%EB%B0%B0%ED%84%B0%EB%A6%AC%20%EC%8B%A4%EC%A0%81%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=%EB%B0%94%EC%9D%B4%EC%98%A4%20%EC%A0%9C%EC%95%BD%20%EC%8B%A4%EC%A0%81%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=%EC%9E%90%EB%8F%99%EC%B0%A8%20%EC%A0%84%EA%B8%B0%EC%B0%A8%20%EC%8B%A4%EC%A0%81%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
    "https://www.investing.com/rss/news_25.rss",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
    "https://www.sec.gov/news/pressreleases.rss",
    "https://openai.com/blog/rss.xml",
    "https://openai.com/news/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://aws.amazon.com/blogs/machine-learning/feed/",
    "https://blog.google/technology/ai/rss/",
    "https://deepmind.google/blog/rss.xml",
    "https://research.google/blog/rss/",
    "https://blogs.nvidia.com/feed/",
    "https://news.mit.edu/rss/topic/artificial-intelligence2",
    "https://artificialintelligence-news.com/feed/",
]


async def check_feed(
    client: httpx.AsyncClient, url: str
) -> tuple[str, int, int, str | None]:
    try:
        response = await client.get(url)
        parsed = feedparser.parse(response.text)
        return url, response.status_code, len(parsed.entries), None
    except Exception as exc:  # noqa: BLE001
        return url, 0, 0, str(exc)


async def main() -> None:
    async with httpx.AsyncClient(
        timeout=10,
        headers={"User-Agent": "ysj.brief feed validator"},
        follow_redirects=True,
    ) as client:
        results = await asyncio.gather(*(check_feed(client, url) for url in FEEDS))

    failed = False
    for url, status_code, entry_count, error in results:
        ok = status_code == 200 and entry_count > 0 and error is None
        failed = failed or not ok
        marker = "OK" if ok else "FAIL"
        print(
            f"{marker} {status_code} entries={entry_count} {url}{' ' + error if error else ''}"
        )

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
