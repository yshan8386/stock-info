from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class RiskStatus(BaseModel):
    name: str
    status: Literal["ok", "watch", "blocked"]
    message: str


class TradingSettingsResponse(BaseModel):
    batch_enabled: bool
    live_trading_enabled: bool
    selected_strategy_ids: list[str]
    batch_interval_seconds: int


class TradingSettingsUpdate(BaseModel):
    batch_enabled: bool | None = None
    live_trading_enabled: bool | None = None
    selected_strategy_ids: list[str] | None = None
    batch_interval_seconds: int | None = None


class TradingSignalResponse(BaseModel):
    id: int
    strategy_id: str
    symbol: str
    name: str
    side: str
    signal: str
    current_price: float
    trigger_price: float
    confidence: float
    execution_mode: str
    status: str
    risk_note: str
    created_at: datetime


class BatchStatus(BaseModel):
    is_running: bool
    last_run_at: datetime | None
    last_run_status: str | None
    captured_signal_count: int
    message: str


class BatchRunResponse(BaseModel):
    status: str
    captured_signal_count: int
    signals: list[TradingSignalResponse]
    message: str


class PositionDashboard(BaseModel):
    mode: Literal["read_only", "paper", "live"]
    trading_enabled: bool
    as_of: datetime
    settings: TradingSettingsResponse
    batch: BatchStatus
    risk_statuses: list[RiskStatus]
    recent_signals: list[TradingSignalResponse]
