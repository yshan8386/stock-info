import asyncio
from datetime import date
import logging

from app.database import SessionLocal
from app.services.briefing_generator import generate_daily_briefing
from app.services.locks import advisory_lock
from app.services.rss_collector import collect_all_feeds

LOCK_RSS = 4242001
LOCK_BRIEFING = 4242002
logger = logging.getLogger(__name__)


def collect_rss_feeds_job() -> None:
    with SessionLocal() as db:
        with advisory_lock(db, LOCK_RSS) as acquired:
            if not acquired:
                logger.info("RSS collection skipped because lock is already held")
                return
            result = asyncio.run(collect_all_feeds(db))
            logger.info("RSS collection completed: %s", result)


def generate_daily_briefing_job() -> None:
    with SessionLocal() as db:
        with advisory_lock(db, LOCK_BRIEFING) as acquired:
            if not acquired:
                logger.info("Daily briefing generation skipped because lock is already held")
                return
            briefing = generate_daily_briefing(db, date.today())
            logger.info(
                "Daily briefing generated: date=%s model=%s source_article_count=%s",
                briefing.briefing_date,
                briefing.model_used,
                briefing.source_article_count,
            )
