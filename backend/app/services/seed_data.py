from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GlossaryCategory, GlossaryTerm, RssFeed

FEEDS = [
    ("GeekNews", "https://news.hada.io/rss/news", "dev", "ko"),
    ("토스 기술 블로그", "https://toss.tech/rss.xml", "dev", "ko"),
    ("카카오 기술 블로그", "https://tech.kakao.com/feed/", "dev", "ko"),
    ("우아한형제들 기술 블로그", "https://techblog.woowahan.com/feed/", "dev", "ko"),
    ("NHN Cloud Meetup", "https://meetup.nhncloud.com/rss", "dev", "ko"),
    ("GitHub Blog", "https://github.blog/feed/", "dev", "en"),
    ("AWS News Blog", "https://aws.amazon.com/blogs/aws/feed/", "dev", "en"),
    ("Microsoft for Developers", "https://devblogs.microsoft.com/feed/", "dev", "en"),
    ("React Status", "https://react.statuscode.com/rss", "dev", "en"),
    ("JavaScript Weekly", "https://javascriptweekly.com/rss", "dev", "en"),
    ("매일경제 금융", "https://www.mk.co.kr/rss/30100041/", "investment", "ko"),
    ("한국경제 증권", "https://www.hankyung.com/feed/finance", "investment", "ko"),
    ("한국경제 경제", "https://www.hankyung.com/feed/economy", "investment", "ko"),
    ("연합뉴스 경제", "https://www.yna.co.kr/rss/economy.xml", "investment", "ko"),
    ("아시아경제 증권", "https://www.asiae.co.kr/rss/stock.htm", "investment", "ko"),
    (
        "반도체 섹터 뉴스",
        "https://news.google.com/rss/search?q=%EB%B0%98%EB%8F%84%EC%B2%B4%20%EC%8B%A4%EC%A0%81%20%EC%88%98%EC%B6%9C%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
        "investment",
        "ko",
    ),
    (
        "2차전지 섹터 뉴스",
        "https://news.google.com/rss/search?q=2%EC%B0%A8%EC%A0%84%EC%A7%80%20%EB%B0%B0%ED%84%B0%EB%A6%AC%20%EC%8B%A4%EC%A0%81%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
        "investment",
        "ko",
    ),
    (
        "바이오 섹터 뉴스",
        "https://news.google.com/rss/search?q=%EB%B0%94%EC%9D%B4%EC%98%A4%20%EC%A0%9C%EC%95%BD%20%EC%8B%A4%EC%A0%81%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
        "investment",
        "ko",
    ),
    (
        "자동차 섹터 뉴스",
        "https://news.google.com/rss/search?q=%EC%9E%90%EB%8F%99%EC%B0%A8%20%EC%A0%84%EA%B8%B0%EC%B0%A8%20%EC%8B%A4%EC%A0%81%20%EC%BD%94%EC%8A%A4%ED%94%BC&hl=ko&gl=KR&ceid=KR:ko",
        "investment",
        "ko",
    ),
    (
        "Investing.com Stock Market News",
        "https://www.investing.com/rss/news_25.rss",
        "investment",
        "en",
    ),
    (
        "MarketWatch Top Stories",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "investment",
        "en",
    ),
    (
        "CNBC Markets",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=15839069",
        "investment",
        "en",
    ),
    (
        "SEC Press Releases",
        "https://www.sec.gov/news/pressreleases.rss",
        "investment",
        "en",
    ),
    ("OpenAI Blog", "https://openai.com/blog/rss.xml", "ai", "en"),
    ("OpenAI News", "https://openai.com/news/rss.xml", "ai", "en"),
    ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml", "ai", "en"),
    (
        "AWS Machine Learning Blog",
        "https://aws.amazon.com/blogs/machine-learning/feed/",
        "ai",
        "en",
    ),
    ("Google AI Blog", "https://blog.google/technology/ai/rss/", "ai", "en"),
    ("Google DeepMind News", "https://deepmind.google/blog/rss.xml", "ai", "en"),
    ("Google Research", "https://research.google/blog/rss/", "ai", "en"),
    ("NVIDIA Blog", "https://blogs.nvidia.com/feed/", "ai", "en"),
    (
        "MIT News AI",
        "https://news.mit.edu/rss/topic/artificial-intelligence2",
        "ai",
        "en",
    ),
    ("AI News", "https://artificialintelligence-news.com/feed/", "ai", "en"),
]

INACTIVE_FEED_URLS = [
    "https://dev.to/feed",
    "https://hnrss.org/frontpage",
    "https://www.fool.com/feeds/index.aspx",
    "https://news.google.com/rss/search?q=%EA%B5%AD%EB%82%B4%EC%A6%9D%EC%8B%9C&hl=ko&gl=KR&ceid=KR:ko",
    "https://techblog.woowahan.com/feed/",
]

CATEGORIES = [
    ("기술적 분석", "technical", "tech", 1),
    ("성과 지표", "performance", "perf", 2),
    ("기본적 분석", "fundamental", "fund", 3),
    ("주문/거래", "trading", "trade", 4),
    ("전략", "strategy", "strat", 5),
]

TERMS = [
    (
        "technical",
        "이동평균선",
        "Moving Average (MA)",
        "일정 기간 주가의 평균을 이은 선",
        "SMA = (P1 + P2 + ... + Pn) / n",
    ),
    (
        "technical",
        "RSI",
        "Relative Strength Index",
        "과매수/과매도를 판단하는 모멘텀 지표",
        "RSI = 100 - (100 / (1 + RS))",
    ),
    (
        "technical",
        "MACD",
        "Moving Average Convergence Divergence",
        "이동평균의 수렴과 발산을 나타내는 추세 지표",
        "MACD = EMA(12) - EMA(26)",
    ),
    (
        "technical",
        "볼린저 밴드",
        "Bollinger Bands",
        "이동평균 주위에 표준편차 밴드를 그린 변동성 지표",
        "상단 = SMA(20) + 2σ",
    ),
    (
        "performance",
        "MDD",
        "Maximum Drawdown",
        "투자 기간 중 고점 대비 최대 하락폭",
        "MDD = (고점 - 저점) / 고점 × 100",
    ),
    (
        "performance",
        "샤프 비율",
        "Sharpe Ratio",
        "위험 대비 초과 수익률을 나타내는 지표",
        "Sharpe = (Rp - Rf) / σp",
    ),
    (
        "performance",
        "CAGR",
        "Compound Annual Growth Rate",
        "연평균 복합 성장률",
        "CAGR = (최종값/초기값)^(1/n) - 1",
    ),
    (
        "fundamental",
        "PER",
        "Price to Earnings Ratio",
        "주가수익비율",
        "PER = 주가 / EPS",
    ),
    (
        "trading",
        "손절",
        "Stop Loss",
        "손실을 제한하기 위해 미리 정한 가격에 매도하는 것",
        None,
    ),
    (
        "trading",
        "트레일링 스탑",
        "Trailing Stop",
        "고점 대비 일정 비율 하락 시 매도하는 동적 손절",
        None,
    ),
    (
        "strategy",
        "이평선 교차 전략",
        "Moving Average Crossover",
        "단기/장기 이동평균의 교차로 매매 시점을 판단하는 전략",
        None,
    ),
    (
        "strategy",
        "변동성 돌파 전략",
        "Volatility Breakout",
        "전일 변동폭의 일정 비율을 돌파하면 매수하는 단기 전략",
        None,
    ),
]


def seed_initial_data(db: Session) -> None:
    for name, url, category, language in FEEDS:
        feed = db.scalar(select(RssFeed).where(RssFeed.url == url))
        if feed is None:
            db.add(RssFeed(name=name, url=url, category=category, language=language))
        else:
            feed.name = name
            feed.category = category
            feed.language = language
            feed.is_active = True

    for url in INACTIVE_FEED_URLS:
        feed = db.scalar(select(RssFeed).where(RssFeed.url == url))
        if feed is not None:
            feed.is_active = False

    category_by_slug: dict[str, GlossaryCategory] = {}
    for name, slug, icon, sort_order in CATEGORIES:
        category = db.scalar(
            select(GlossaryCategory).where(GlossaryCategory.slug == slug)
        )
        if category is None:
            category = GlossaryCategory(
                name=name, slug=slug, icon=icon, sort_order=sort_order
            )
            db.add(category)
            db.flush()
        category_by_slug[slug] = category

    for slug, term_ko, term_en, short_desc, formula in TERMS:
        if not db.scalar(select(GlossaryTerm).where(GlossaryTerm.term_ko == term_ko)):
            db.add(
                GlossaryTerm(
                    category_id=category_by_slug[slug].id,
                    term_ko=term_ko,
                    term_en=term_en,
                    short_desc=short_desc,
                    detail_markdown=f"{short_desc}\n\n투자 전략을 비교하거나 시장 흐름을 해석할 때 자주 사용하는 개념입니다.",
                    formula=formula,
                    example=None,
                    related_term_ids=[],
                )
            )
    db.commit()
