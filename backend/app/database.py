from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


settings = get_settings()
database_url = _normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args, pool_pre_ping=True)

if database_url.startswith("postgresql"):
    search_path = (
        settings.db_schema
        if settings.db_schema == "public"
        else f"{settings.db_schema}, public"
    )

    @event.listens_for(engine, "connect")
    def set_postgres_search_path(dbapi_connection: object, _: object) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"SET search_path TO {search_path}")
            dbapi_connection.commit()
        except Exception:
            dbapi_connection.rollback()
            raise
        finally:
            cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _quote_postgres_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    from app.models import briefing, feed, glossary, news, user  # noqa: F401

    if database_url.startswith("postgresql") and settings.db_schema != "public":
        schema = _quote_postgres_identifier(settings.db_schema)
        with engine.begin() as connection:
            schema_exists = connection.scalar(
                text(
                    "SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema"
                ),
                {"schema": settings.db_schema},
            )
            if not schema_exists:
                connection.execute(text(f"CREATE SCHEMA {schema}"))

    Base.metadata.create_all(bind=engine)
