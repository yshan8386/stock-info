from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, backtest, brief, dashboard, feeds, glossary, health
from app.config import get_settings
from app.database import SessionLocal, create_db_and_tables
from app.services.seed_data import seed_initial_data


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup() -> None:
        create_db_and_tables()
        with SessionLocal() as db:
            seed_initial_data(db)

    @app.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        if hasattr(exc, "status_code"):
            raise exc
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": str(exc)}})

    app.include_router(health.router)
    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(dashboard.router, prefix=settings.api_prefix)
    app.include_router(backtest.router, prefix=settings.api_prefix)
    app.include_router(brief.router, prefix=settings.api_prefix)
    app.include_router(feeds.router, prefix=settings.api_prefix)
    app.include_router(glossary.router, prefix=settings.api_prefix)
    return app


app = create_app()
