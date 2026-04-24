from datetime import datetime, timedelta
from math import sin, tau

from app.schemas.backtest import AutoBacktestRequest, BacktestConfig, OhlcvCandle
from app.services.backtest_engine import (
    find_price_levels,
    run_pullback_rebound_backtest,
    run_support_resistance_backtest,
)
from app.services.backtest_selector import run_auto_backtest
from app.services.kis_market_data import KIS_OHLCV_ENDPOINTS
from app.services.backtest_strategies import list_strategies


def _candle(day: int, close: float, volume: float = 1_000) -> OhlcvCandle:
    timestamp = datetime(2026, 1, 1) + timedelta(days=day)
    open_ = close * 0.995
    high = close * 1.01
    low = close * 0.99
    return OhlcvCandle(
        timestamp=timestamp, open=open_, high=high, low=low, close=close, volume=volume
    )


def _sample_candles() -> list[OhlcvCandle]:
    candles: list[OhlcvCandle] = []
    for day in range(100):
        close = 105 + sin(day / 12 * tau) * 5
        candles.append(_candle(day, close))

    breakout_prices = [
        108,
        110,
        113,
        116,
        119,
        121,
        123,
        125,
        126,
        128,
        130,
        132,
        131,
        133,
        134,
    ]
    for offset, close in enumerate(breakout_prices, start=100):
        candles.append(_candle(offset, close, volume=2_400))
    return candles


def _pullback_candles() -> list[OhlcvCandle]:
    candles: list[OhlcvCandle] = []
    for day in range(90):
        close = 100 + day * 0.6
        candles.append(_candle(day, close, volume=1_100))

    pullback_sequence = [
        (154, 1_000),
        (152, 950),
        (149, 900),
        (146, 880),
        (144, 860),
        (147, 1_500),
        (150, 1_650),
        (153, 1_700),
        (156, 1_600),
        (159, 1_550),
        (162, 1_450),
    ]
    for offset, (close, volume) in enumerate(pullback_sequence, start=90):
        candles.append(_candle(offset, close, volume=volume))
    return candles


def test_find_price_levels_groups_repeated_swings() -> None:
    config = BacktestConfig(lookback_period=80)

    supports, resistances = find_price_levels(_sample_candles()[:100], config)

    assert supports
    assert resistances
    assert max(level.touches for level in supports) >= 2
    assert max(level.touches for level in resistances) >= 2


def test_support_resistance_backtest_opens_and_closes_trade() -> None:
    result = run_support_resistance_backtest(
        symbol="005930",
        candles=_sample_candles(),
        config=BacktestConfig(
            lookback_period=70, min_volume_ratio=1.05, min_slope_atr=0.0
        ),
    )

    assert result.symbol == "005930"
    assert result.metrics.initial_capital == 10_000_000
    assert result.metrics.trade_count >= 1
    assert result.equity_curve
    assert result.trades[0].entry_price > 0
    assert result.trades[0].exit_price is not None


def test_pullback_rebound_backtest_opens_and_closes_trade() -> None:
    result = run_pullback_rebound_backtest(
        symbol="005930",
        candles=_pullback_candles(),
        config=BacktestConfig(
            lookback_period=70, min_volume_ratio=1.0, min_slope_atr=0.0
        ),
    )

    assert result.symbol == "005930"
    assert result.metrics.trade_count >= 1
    assert result.trades[0].reason == "pullback_rebound"
    assert result.trades[0].exit_price is not None


def test_kis_ohlcv_endpoint_catalog_contains_daily_and_minute_chart_apis() -> None:
    daily = next(item for item in KIS_OHLCV_ENDPOINTS if item.timeframe == "daily")
    minute = next(item for item in KIS_OHLCV_ENDPOINTS if item.timeframe == "minute")

    assert daily.endpoint.endswith("/inquire-daily-itemchartprice")
    assert daily.tr_id == "FHKST03010100"
    assert daily.fields["close"] == "stck_clpr"
    assert minute.endpoint.endswith("/inquire-time-dailychartprice")
    assert minute.tr_id == "FHKST03010230"


def test_auto_backtest_selects_symbols_and_returns_support_resistance_amounts() -> None:
    result = run_auto_backtest(
        AutoBacktestRequest(
            start_date=datetime(2025, 10, 1).date(),
            end_date=datetime(2026, 4, 22).date(),
            initial_capital=10_000_000,
            min_avg_trade_amount=5_000_000_000,
            strategy_ids=["pullback_rebound_v1", "support_resistance_v1"],
        )
    )

    assert result.selected
    assert len(result.strategy_runs) == 2
    assert result.results
    assert result.results[0].supports
    assert result.results[0].resistances
    assert (
        result.results[0].equity_curve[0].timestamp.date() >= result.request.start_date
    )


def test_auto_backtest_filters_symbols_that_exceed_price_cap() -> None:
    result = run_auto_backtest(
        AutoBacktestRequest(
            start_date=datetime(2025, 1, 1).date(),
            end_date=datetime(2025, 12, 31).date(),
            initial_capital=600_000,
            max_symbols=5,
        )
    )

    assert result.selected
    assert all(item.current_price <= 200_000 for item in result.selected)
    assert "207940" not in {item.symbol for item in result.selected}


def test_strategy_registry_contains_pullback_and_support_resistance() -> None:
    strategy_ids = {strategy.id for strategy in list_strategies()}

    assert "pullback_rebound_v1" in strategy_ids
    assert "support_resistance_v1" in strategy_ids
