import asyncio
from datetime import date

from app.database import SessionLocal
from app.services.briefing_generator import generate_daily_briefing
from app.services.locks import advisory_lock
from app.services.rss_collector import collect_all_feeds

LOCK_RSS = 4242001
LOCK_BRIEFING = 4242002


def collect_rss_feeds_job() -> None:
    with SessionLocal() as db:
        with advisory_lock(db, LOCK_RSS) as acquired:
            if not acquired:
                return
            asyncio.run(collect_all_feeds(db))


def generate_daily_briefing_job() -> None:
    with SessionLocal() as db:
        with advisory_lock(db, LOCK_BRIEFING) as acquired:
            if not acquired:
                return
            generate_daily_briefing(db, date.today())

