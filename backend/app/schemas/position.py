from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AccountSummary(BaseModel):
    total_equity: int
    cash: int
    invested_amount: int
    day_pnl: int
    day_pnl_pct: float
    total_pnl: int
    total_pnl_pct: float
    buying_power: int


class RiskStatus(BaseModel):
    name: str
    status: Literal["ok", "watch", "blocked"]
    message: str


class LiveStrategyStatus(BaseModel):
    strategy_id: str
    strategy_label: str
    status: Literal["active", "watching", "paused"]
    allocated_capital: int
    deployed_capital: int
    open_positions: int
    max_positions: int
    unrealized_pnl: int
    unrealized_pnl_pct: float
    next_action: str


class LivePosition(BaseModel):
    symbol: str
    name: str
    strategy_id: str
    quantity: int
    average_price: int
    current_price: int
    market_value: int
    unrealized_pnl: int
    unrealized_pnl_pct: float
    stop_loss: int
    take_profit: int
    entry_reason: str


class WatchSignal(BaseModel):
    symbol: str
    name: str
    strategy_id: str
    signal: str
    current_price: int
    trigger_price: int
    risk_note: str


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
    account: AccountSummary
    risk_statuses: list[RiskStatus]
    strategies: list[LiveStrategyStatus]
    positions: list[LivePosition]
    watchlist: list[WatchSignal]
    recent_signals: list[TradingSignalResponse]
