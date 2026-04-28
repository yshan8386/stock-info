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
    AccountSummary,
    BatchRunResponse,
    BatchStatus,
    LivePosition,
    LiveStrategyStatus,
    PositionDashboard,
    RiskStatus,
    TradingSettingsResponse,
    TradingSettingsUpdate,
    TradingSignalResponse,
    WatchSignal,
)
from app.services.backtest_strategies import list_strategies

router = APIRouter(prefix="/position", tags=["position"], dependencies=[Depends(get_current_user)])

DEFAULT_STRATEGY_IDS = ["pullback_rebound_v1", "support_resistance_v1"]
_FALLBACK_SIGNAL_ID = 0
_FALLBACK_SETTINGS: dict[int, "VolatileSettings"] = {}
_FALLBACK_SIGNALS: dict[int, list[TradingSignalResponse]] = {}
_FALLBACK_LAST_RUN: dict[int, BatchStatus] = {}


@dataclass
class VolatileSettings:
    user_id: int
    batch_enabled: bool = False
    live_trading_enabled: bool = False
    selected_strategy_ids: list[str] = field(default_factory=lambda: list(DEFAULT_STRATEGY_IDS))
    batch_interval_seconds: int = 10

SIGNAL_UNIVERSE = [
    {
        "symbol": "005930",
        "name": "삼성전자",
        "strategy_id": "pullback_rebound_v1",
        "signal": "20일선 눌림 후 거래량 회복",
        "current_price": 72_100,
        "trigger_price": 72_500,
        "risk_note": "반도체 대형주 변동성 확인",
    },
    {
        "symbol": "000660",
        "name": "SK하이닉스",
        "strategy_id": "support_resistance_v1",
        "signal": "전고점 돌파 후 지지 확인",
        "current_price": 234_900,
        "trigger_price": 236_000,
        "risk_note": "갭 상승 이후 추격 진입 주의",
    },
    {
        "symbol": "068270",
        "name": "셀트리온",
        "strategy_id": "breakout_volume_v1",
        "signal": "거래대금 동반 박스권 상단 돌파",
        "current_price": 181_200,
        "trigger_price": 184_000,
        "risk_note": "제약 업종 변동성 확대",
    },
    {
        "symbol": "051910",
        "name": "LG화학",
        "strategy_id": "trend_follow_v1",
        "signal": "중기 이동평균 재정렬 대기",
        "current_price": 364_500,
        "trigger_price": 371_000,
        "risk_note": "거래대금 회복 필요",
    },
    {
        "symbol": "035720",
        "name": "카카오",
        "strategy_id": "rsi_reversal_v1",
        "signal": "RSI 과매도 탈출 후보",
        "current_price": 50_350,
        "trigger_price": 51_200,
        "risk_note": "뉴스 이벤트 민감도 높음",
    },
]


def _now() -> datetime:
    return datetime.now(ZoneInfo(get_settings().timezone))


def _strategy_labels() -> dict[str, str]:
    return {strategy.id: strategy.label for strategy in list_strategies()}


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
        return _FALLBACK_SIGNALS.get(user_id, [])[:limit]


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
    global _FALLBACK_SIGNAL_ID
    settings = _get_or_create_settings(db, user.id)
    if not settings.batch_enabled:
        return BatchRunResponse(status="skipped", captured_signal_count=0, signals=[], message="배치 실행이 꺼져 있습니다.")

    selected_ids = settings.selected_strategy_ids or DEFAULT_STRATEGY_IDS
    execution_mode = "live_order_requested" if settings.live_trading_enabled else "signal_only"
    status = "ready_for_live_order" if settings.live_trading_enabled else "captured"
    started_at = _now()
    created: list[TradingSignal] = []
    cycle = started_at.second % max(len(SIGNAL_UNIVERSE), 1)
    candidates = SIGNAL_UNIVERSE[cycle:] + SIGNAL_UNIVERSE[:cycle]

    for index, item in enumerate(candidates):
        if item["strategy_id"] not in selected_ids:
            continue
        current_price = float(item["current_price"]) + (started_at.second % 5) * 10
        confidence = round(0.72 + min(index, 3) * 0.04, 2)
        if not isinstance(settings, TradingSettings):
            _FALLBACK_SIGNAL_ID += 1
            response = TradingSignalResponse(
                id=_FALLBACK_SIGNAL_ID,
                strategy_id=item["strategy_id"],
                symbol=item["symbol"],
                name=item["name"],
                side="buy",
                signal=item["signal"],
                current_price=current_price,
                trigger_price=float(item["trigger_price"]),
                confidence=confidence,
                execution_mode=execution_mode,
                status=status,
                risk_note=item["risk_note"],
                created_at=started_at,
            )
            _FALLBACK_SIGNALS.setdefault(user.id, []).insert(0, response)
            if len(_FALLBACK_SIGNALS[user.id]) > 50:
                _FALLBACK_SIGNALS[user.id] = _FALLBACK_SIGNALS[user.id][:50]
            if len(_FALLBACK_SIGNALS[user.id]) >= 3:
                break
            continue
        signal = TradingSignal(
            user_id=user.id,
            strategy_id=item["strategy_id"],
            symbol=item["symbol"],
            name=item["name"],
            side="buy",
            signal=item["signal"],
            current_price=current_price,
            trigger_price=float(item["trigger_price"]),
            confidence=confidence,
            execution_mode=execution_mode,
            status=status,
            risk_note=item["risk_note"],
        )
        db.add(signal)
        created.append(signal)
        if len(created) >= 3:
            break

    if not isinstance(settings, TradingSettings):
        captured = _FALLBACK_SIGNALS.get(user.id, [])[:3]
        batch_status = BatchStatus(
            is_running=settings.batch_enabled,
            last_run_at=_now(),
            last_run_status="completed",
            captured_signal_count=len(captured),
            message="새 실전투자 테이블이 없어 임시 저장소에 시그널을 보관했습니다.",
        )
        _FALLBACK_LAST_RUN[user.id] = batch_status
        message = "실투자 요청 대상으로 표시했습니다." if settings.live_trading_enabled else "실투자 없이 시그널만 임시 저장했습니다."
        return BatchRunResponse(status="completed", captured_signal_count=len(captured), signals=captured, message=message)

    run = TradingBatchRun(
        user_id=user.id,
        status="completed",
        live_trading_enabled=settings.live_trading_enabled,
        selected_strategy_ids=selected_ids,
        captured_signal_count=len(created),
        started_at=started_at,
        finished_at=_now(),
    )
    db.add(run)
    db.commit()
    for signal in created:
        db.refresh(signal)

    message = "실투자 요청 대상으로 표시했습니다." if settings.live_trading_enabled else "실투자 없이 시그널만 DB에 저장했습니다."
    return BatchRunResponse(status="completed", captured_signal_count=len(created), signals=[_signal_response(signal) for signal in created], message=message)


@router.get("/dashboard", response_model=PositionDashboard)
def get_position_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PositionDashboard:
    settings = _get_or_create_settings(db, user.id)
    selected_ids = settings.selected_strategy_ids or DEFAULT_STRATEGY_IDS
    strategy_labels = _strategy_labels()
    recent_signals = _recent_signals(db, user.id)
    running_adjustment = (_now().second % 8) * 1_250 if settings.batch_enabled else 0

    account = AccountSummary(
        total_equity=2_083_500 + running_adjustment,
        cash=683_500,
        invested_amount=1_400_000,
        day_pnl=18_500 + running_adjustment,
        day_pnl_pct=round((18_500 + running_adjustment) / 2_065_000 * 100, 2),
        total_pnl=83_500 + running_adjustment,
        total_pnl_pct=round((83_500 + running_adjustment) / 2_000_000 * 100, 2),
        buying_power=683_500,
    )
    live_strategies = [
        LiveStrategyStatus(
            strategy_id=strategy_id,
            strategy_label=strategy_labels.get(strategy_id, strategy_id),
            status="active" if settings.batch_enabled else "paused",
            allocated_capital=1_000_000,
            deployed_capital=720_000 if strategy_id == "pullback_rebound_v1" else 420_000,
            open_positions=2 if strategy_id == "pullback_rebound_v1" else 1,
            max_positions=3,
            unrealized_pnl=58_200 if strategy_id == "pullback_rebound_v1" else 25_300,
            unrealized_pnl_pct=8.08 if strategy_id == "pullback_rebound_v1" else 3.72,
            next_action="배치가 켜져 있어 다음 주기에 진입 후보를 갱신합니다." if settings.batch_enabled else "배치 실행이 꺼져 있습니다.",
        )
        for strategy_id in selected_ids
    ]
    watchlist = [
        WatchSignal(
            symbol=item["symbol"],
            name=item["name"],
            strategy_id=item["strategy_id"],
            signal=item["signal"],
            current_price=float(item["current_price"]),
            trigger_price=float(item["trigger_price"]),
            risk_note=item["risk_note"],
        )
        for item in SIGNAL_UNIVERSE
        if item["strategy_id"] in selected_ids
    ][:5]

    return PositionDashboard(
        mode="live" if settings.live_trading_enabled else "paper",
        trading_enabled=settings.live_trading_enabled,
        as_of=_now(),
        settings=_settings_response(settings),
        batch=_latest_batch_status(db, user.id, settings),
        account=account,
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
        strategies=live_strategies,
        positions=[
            LivePosition(
                symbol="005930",
                name="삼성전자",
                strategy_id="pullback_rebound_v1",
                quantity=8,
                average_price=70_200,
                current_price=72_100 + running_adjustment / 100,
                market_value=576_800 + running_adjustment,
                unrealized_pnl=15_200 + running_adjustment,
                unrealized_pnl_pct=round((15_200 + running_adjustment) / 561_600 * 100, 2),
                stop_loss=67_800,
                take_profit=77_400,
                entry_reason="눌림 후 거래량 회복",
            )
        ],
        watchlist=watchlist,
        recent_signals=recent_signals,
    )
