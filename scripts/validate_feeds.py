import asyncio

import feedparser
import httpx

FEEDS = [
    "https://news.hada.io/rss/news",
    "https://toss.tech/rss.xml",
    "https://tech.kakao.com/feed/",
    "https://techblog.woowahan.com/feed/",
    "https://meetup.nhncloud.com/rss",
    "https://dev.to/feed",
    "https://hnrss.org/frontpage",
    "https://react.statuscode.com/rss",
    "https://javascriptweekly.com/rss",
    "https://www.mk.co.kr/rss/30100041/",
    "https://news.google.com/rss/search?q=%EA%B5%AD%EB%82%B4%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko",
    "https://www.investing.com/rss/news_25.rss",
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://www.fool.com/feeds/index.aspx",
    "https://openai.com/blog/rss.xml",
    "https://huggingface.co/blog/feed.xml",
    "https://blog.google/technology/ai/rss/",
    "https://artificialintelligence-news.com/feed/",
]


async def check_feed(client: httpx.AsyncClient, url: str) -> tuple[str, int, int, str | None]:
    try:
        response = await client.get(url)
        parsed = feedparser.parse(response.text)
        return url, response.status_code, len(parsed.entries), None
    except Exception as exc:  # noqa: BLE001
        return url, 0, 0, str(exc)


async def main() -> None:
    async with httpx.AsyncClient(timeout=10, headers={"User-Agent": "ysj.brief feed validator"}, follow_redirects=True) as client:
        results = await asyncio.gather(*(check_feed(client, url) for url in FEEDS))

    failed = False
    for url, status_code, entry_count, error in results:
        ok = status_code == 200 and entry_count > 0 and error is None
        failed = failed or not ok
        marker = "OK" if ok else "FAIL"
        print(f"{marker} {status_code} entries={entry_count} {url}{' ' + error if error else ''}")

    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
