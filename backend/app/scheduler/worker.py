import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import SessionLocal, create_db_and_tables
from app.scheduler.jobs import collect_rss_feeds_job, generate_afternoon_briefing_job, generate_morning_briefing_job
from app.services.seed_data import seed_initial_data


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    create_db_and_tables()
    with SessionLocal() as db:
        seed_initial_data(db)

    scheduler = BlockingScheduler(timezone=settings.timezone)
    scheduler.add_job(collect_rss_feeds_job, "cron", minute=5, id="collect_rss_feeds", replace_existing=True)
    if settings.scheduled_briefing_enabled:
        scheduler.add_job(
            generate_morning_briefing_job,
            CronTrigger(hour=7, minute=30, timezone=settings.timezone),
            id="generate_morning_briefing",
            replace_existing=True,
        )
        scheduler.add_job(
            generate_afternoon_briefing_job,
            CronTrigger(hour=16, minute=30, timezone=settings.timezone),
            id="generate_afternoon_briefing",
            replace_existing=True,
        )
    scheduler.start()


if __name__ == "__main__":
    main()
