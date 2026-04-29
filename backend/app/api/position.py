from datetime import datetime
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import TradingBatchRun, TradingSettings, TradingSignal, User
from app.schemas.position import (
    BatchRunResponse,
    BatchStatus,
    PositionDashboard,
    RiskStatus,
    TradingSettingsResponse,
    TradingSettingsUpdate,
    TradingSignalResponse,
)
from app.services.backtest_strategies import list_strategies

router = APIRouter(prefix="/position", tags=["position"], dependencies=[Depends(get_current_user)])

DEFAULT_STRATEGY_IDS = ["pullback_rebound_v1", "support_resistance_v1"]
_FALLBACK_SETTINGS: dict[int, "VolatileSettings"] = {}
_FALLBACK_LAST_RUN: dict[int, BatchStatus] = {}


@dataclass
class VolatileSettings:
    user_id: int
    batch_enabled: bool = False
    live_trading_enabled: bool = False
    selected_strategy_ids: list[str] = field(default_factory=lambda: list(DEFAULT_STRATEGY_IDS))
    batch_interval_seconds: int = 10


def _now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().timezone))


def _get_or_create_settings(db: Session, user_id: int) -> TradingSettings:
    try:
        settings = db.scalar(select(TradingSettings).where(TradingSettings.user_id == user_id))
        if settings is not None:
            return settings
        settings = TradingSettings(
            user_id=user_id,
            batch_enabled=False,
            live_trading_enabled=False,
            selected_strategy_ids=DEFAULT_STRATEGY_IDS,
            batch_interval_seconds=10,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings
    except SQLAlchemyError:
        db.rollback()
        return _FALLBACK_SETTINGS.setdefault(user_id, VolatileSettings(user_id=user_id))  # type: ignore[return-value]


def _settings_response(settings: TradingSettings) -> TradingSettingsResponse:
    return TradingSettingsResponse(
        batch_enabled=settings.batch_enabled,
        live_trading_enabled=settings.live_trading_enabled,
        selected_strategy_ids=settings.selected_strategy_ids or DEFAULT_STRATEGY_IDS,
        batch_interval_seconds=settings.batch_interval_seconds,
    )


def _signal_response(signal: TradingSignal) -> TradingSignalResponse:
    return TradingSignalResponse(
        id=signal.id,
        strategy_id=signal.strategy_id,
        symbol=signal.symbol,
        name=signal.name,
        side=signal.side,
        signal=signal.signal,
        current_price=signal.current_price,
        trigger_price=signal.trigger_price,
        confidence=signal.confidence,
        execution_mode=signal.execution_mode,
        status=signal.status,
        risk_note=signal.risk_note,
        created_at=signal.created_at,
    )


def _latest_batch_status(db: Session, user_id: int, settings: TradingSettings) -> BatchStatus:
    try:
        last_run = db.scalar(
            select(TradingBatchRun)
            .where(TradingBatchRun.user_id == user_id)
            .order_by(desc(TradingBatchRun.started_at))
            .limit(1)
        )
    except SQLAlchemyError:
        db.rollback()
        last_status = _FALLBACK_LAST_RUN.get(user_id)
        if last_status is not None:
            return last_status
        last_run = None
    return BatchStatus(
        is_running=settings.batch_enabled,
        last_run_at=last_run.finished_at if last_run else None,
        last_run_status=last_run.status if last_run else None,
        captured_signal_count=last_run.captured_signal_count if last_run else 0,
        message=(
            "배치가 켜져 있어 화면 갱신 주기마다 시그널을 탐색합니다."
            if settings.batch_enabled
            else "배치가 꺼져 있어 새 시그널을 탐색하지 않습니다."
        ),
    )


def _recent_signals(db: Session, user_id: int, limit: int = 12) -> list[TradingSignalResponse]:
    try:
        signals = db.scalars(
            select(TradingSignal)
            .where(TradingSignal.user_id == user_id)
            .order_by(desc(TradingSignal.created_at), desc(TradingSignal.id))
            .limit(limit)
        )
        return [_signal_response(signal) for signal in signals]
    except SQLAlchemyError:
        db.rollback()
        return []


@router.get("/settings", response_model=TradingSettingsResponse)
def get_trading_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TradingSettingsResponse:
    return _settings_response(_get_or_create_settings(db, user.id))


@router.patch("/settings", response_model=TradingSettingsResponse)
def update_trading_settings(
    request: TradingSettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TradingSettingsResponse:
    settings = _get_or_create_settings(db, user.id)
    available_ids = {strategy.id for strategy in list_strategies()}
    if request.batch_enabled is not None:
        settings.batch_enabled = request.batch_enabled
    if request.live_trading_enabled is not None:
        settings.live_trading_enabled = request.live_trading_enabled
    if request.selected_strategy_ids is not None:
        selected = list(dict.fromkeys(strategy_id for strategy_id in request.selected_strategy_ids if strategy_id))
        unknown = [strategy_id for strategy_id in selected if strategy_id not in available_ids]
        if unknown:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 전략입니다: {', '.join(unknown)}")
        settings.selected_strategy_ids = selected or DEFAULT_STRATEGY_IDS
    if request.batch_interval_seconds is not None:
        settings.batch_interval_seconds = min(max(request.batch_interval_seconds, 5), 60)
    if isinstance(settings, TradingSettings):
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return _settings_response(settings)


@router.post("/batch/run", response_model=BatchRunResponse)
def run_position_batch(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BatchRunResponse:
    settings = _get_or_create_settings(db, user.id)
    if not settings.batch_enabled:
        return BatchRunResponse(status="skipped", captured_signal_count=0, signals=[], message="배치 실행이 꺼져 있습니다.")

    selected_ids = settings.selected_strategy_ids or DEFAULT_STRATEGY_IDS
    started_at = _now()

    if not isinstance(settings, TradingSettings):
        batch_status = BatchStatus(
            is_running=settings.batch_enabled,
            last_run_at=_now(),
            last_run_status="completed",
            captured_signal_count=0,
            message="실전 시그널 생성기가 아직 연결되지 않아 새 시그널이 없습니다.",
        )
        _FALLBACK_LAST_RUN[user.id] = batch_status
        return BatchRunResponse(status="completed", captured_signal_count=0, signals=[], message=batch_status.message)

    run = TradingBatchRun(
        user_id=user.id,
        status="completed",
        live_trading_enabled=settings.live_trading_enabled,
        selected_strategy_ids=selected_ids,
        captured_signal_count=0,
        started_at=started_at,
        finished_at=_now(),
    )
    db.add(run)
    db.commit()

    message = "실전 시그널 생성기가 아직 연결되지 않아 새 시그널이 없습니다."
    return BatchRunResponse(status="completed", captured_signal_count=0, signals=[], message=message)


@router.get("/dashboard", response_model=PositionDashboard)
def get_position_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PositionDashboard:
    settings = _get_or_create_settings(db, user.id)
    selected_ids = settings.selected_strategy_ids or DEFAULT_STRATEGY_IDS
    recent_signals = _recent_signals(db, user.id)

    return PositionDashboard(
        mode="live" if settings.live_trading_enabled else "paper",
        trading_enabled=settings.live_trading_enabled,
        as_of=_now(),
        settings=_settings_response(settings),
        batch=_latest_batch_status(db, user.id, settings),
        risk_statuses=[
            RiskStatus(
                name="배치 실행",
                status="ok" if settings.batch_enabled else "watch",
                message="켜짐" if settings.batch_enabled else "꺼짐",
            ),
            RiskStatus(
                name="실투자",
                status="watch" if settings.live_trading_enabled else "blocked",
                message="실투자 요청 모드입니다." if settings.live_trading_enabled else "실투자 없이 시그널만 저장합니다.",
            ),
            RiskStatus(name="전략 선택", status="ok", message=f"{len(selected_ids)}개 전략 감시 중"),
            RiskStatus(name="주문 어댑터", status="watch", message="KIS 주문 연동 전까지 주문 요청 상태로만 기록합니다."),
        ],
        recent_signals=recent_signals,
    )
