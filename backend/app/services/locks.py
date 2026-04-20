from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session


@contextmanager
def advisory_lock(db: Session, lock_id: int) -> Iterator[bool]:
    dialect = db.bind.dialect.name if db.bind is not None else ""
    if dialect != "postgresql":
        yield True
        return

    acquired = db.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": lock_id}).scalar()
    if not acquired:
        yield False
        return
    try:
        yield True
    finally:
        db.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
        db.commit()

