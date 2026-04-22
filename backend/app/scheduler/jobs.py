import asyncio
from datetime import datetime
import logging
from zoneinfo import ZoneInfo

from app.config import get_settings
from app.database import SessionLocal
from app.services.briefing_generator import BRIEFING_TYPE_AFTERNOON, BRIEFING_TYPE_MORNING, generate_daily_briefing
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


def generate_daily_briefing_job(briefing_type: str = BRIEFING_TYPE_MORNING) -> None:
    settings = get_settings()
    target_date = datetime.now(ZoneInfo(settings.timezone)).date()
    with SessionLocal() as db:
        with advisory_lock(db, LOCK_BRIEFING) as acquired:
            if not acquired:
                logger.info("Daily briefing generation skipped because lock is already held")
                return
            briefing = generate_daily_briefing(db, target_date, briefing_type)
            logger.info(
                "Daily briefing generated: date=%s type=%s model=%s source_article_count=%s",
                briefing.briefing_date,
                briefing.briefing_type,
                briefing.model_used,
                briefing.source_article_count,
            )


def generate_morning_briefing_job() -> None:
    generate_daily_briefing_job(BRIEFING_TYPE_MORNING)


def generate_afternoon_briefing_job() -> None:
    generate_daily_briefing_job(BRIEFING_TYPE_AFTERNOON)
