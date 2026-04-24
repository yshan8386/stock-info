from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OhlcvCandle(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)

    @model_validator(mode="after")
    def prices_must_form_a_valid_candle(self):
        if self.high < max(self.open, self.close, self.low):
            raise ValueError(
                "high must be greater than or equal to open, close, and low"
            )
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low must be less than or equal to open, close, and high")
        return self


class BacktestConfig(BaseModel):
    initial_capital: float = Field(default=10_000_000, gt=0)
    position_size_pct: float = Field(default=0.95, gt=0, le=1)
    lookback_period: int = Field(default=80, ge=30, le=260)
    swing_window: int = Field(default=3, ge=2, le=10)
    slope_period: int = Field(default=20, ge=5, le=80)
    volume_period: int = Field(default=20, ge=5, le=80)
    min_volume_ratio: float = Field(default=1.15, ge=0)
    min_slope_atr: float = Field(default=0.02)
    level_tolerance_pct: float = Field(default=0.01, gt=0, le=0.1)
    breakout_buffer_pct: float = Field(default=0.003, ge=0, le=0.05)
    stop_loss_buffer_pct: float = Field(default=0.006, ge=0, le=0.1)
    risk_reward_ratio: float = Field(default=1.8, gt=0)
    commission_rate: float = Field(default=0.00015, ge=0, le=0.01)
    tax_rate: float = Field(default=0.002, ge=0, le=0.01)
    slippage_pct: float = Field(default=0.0005, ge=0, le=0.02)


class ManualBacktestRequest(BaseModel):
    symbol: str = Field(default="MANUAL", min_length=1, max_length=20)
    candles: list[OhlcvCandle] = Field(min_length=60)
    config: BacktestConfig = Field(default_factory=BacktestConfig)


class PriceLevel(BaseModel):
    price: float
    kind: Literal["support", "resistance"]
    strength: float
    touches: int
    last_touched_at: datetime | None = None


class BacktestTrade(BaseModel):
    entry_at: datetime
    entry_price: float
    quantity: int
    reason: str
    stop_loss: float
    take_profit: float
    exit_at: datetime | None = None
    exit_price: float | None = None
    exit_reason: str | None = None
    pnl: float | None = None
    pnl_pct: float | None = None


class EquityPoint(BaseModel):
    timestamp: datetime
    equity: float
    cash: float
    position_value: float
    close: float


class BacktestMetrics(BaseModel):
    initial_capital: float
    final_capital: float
    total_return_pct: float
    max_drawdown_pct: float
    trade_count: int
    win_rate_pct: float
    profit_factor: float
    sharpe_ratio: float


class BacktestResponse(BaseModel):
    symbol: str
    symbol_name: str | None = None
    avg_trade_amount: float | None = None
    metrics: BacktestMetrics
    supports: list[PriceLevel]
    resistances: list[PriceLevel]
    trades: list[BacktestTrade]
    equity_curve: list[EquityPoint]
    notes: list[str]


class StrategyInfo(BaseModel):
    id: str
    label: str
    description: str


class StrategyComparisonSummary(BaseModel):
    strategy_id: str
    strategy_label: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    max_drawdown_pct: float
    trade_count: int
    win_rate_pct: float
    sharpe_ratio: float


class StrategyBacktestRun(BaseModel):
    strategy: StrategyInfo
    summary: StrategyComparisonSummary
    results: list[BacktestResponse]


class AutoBacktestRequest(BaseModel):
    start_date: date
    end_date: date
    initial_capital: float = Field(default=10_000_000, gt=0)
    min_avg_trade_amount: float = Field(default=5_000_000_000, ge=0)
    max_symbols: int = Field(default=50, ge=1, le=50)
    strategy_ids: list[str] = Field(default_factory=lambda: ["pullback_rebound_v1"])

    @model_validator(mode="after")
    def dates_must_be_valid(self):
        if self.start_date >= self.end_date:
            raise ValueError("end_date must be after start_date")
        strategy_ids = [
            strategy_id.strip()
            for strategy_id in self.strategy_ids
            if strategy_id.strip()
        ]
        if not strategy_ids:
            raise ValueError("at least one strategy_id is required")
        self.strategy_ids = list(dict.fromkeys(strategy_ids))
        return self


class StockSelectionItem(BaseModel):
    symbol: str
    name: str
    avg_trade_amount: float
    current_price: float
    market_cap: float | None = None
    allocated_budget: float | None = None
    max_buyable_quantity: int | None = None
    score: float
    reason: str


class AutoBacktestResponse(BaseModel):
    request: AutoBacktestRequest
    selected: list[StockSelectionItem]
    strategy_runs: list[StrategyBacktestRun]
    results: list[BacktestResponse]
    notes: list[str]


class KisOhlcvEndpointInfo(BaseModel):
    market: str
    timeframe: str
    endpoint: str
    tr_id: str
    max_rows_per_call: int
    output: str
    fields: dict[str, str]
