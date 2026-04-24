from __future__ import annotations

from datetime import date
from math import sqrt
from statistics import mean, pstdev

from app.schemas.backtest import (
    BacktestConfig,
    BacktestMetrics,
    BacktestResponse,
    BacktestTrade,
    EquityPoint,
    OhlcvCandle,
    PriceLevel,
)


def _avg(values: list[float], default: float = 0.0) -> float:
    return mean(values) if values else default


def _round_money(value: float) -> float:
    return round(float(value), 2)


def _true_ranges(candles: list[OhlcvCandle]) -> list[float]:
    ranges: list[float] = []
    previous_close: float | None = None
    for candle in candles:
        if previous_close is None:
            ranges.append(candle.high - candle.low)
        else:
            ranges.append(
                max(
                    candle.high - candle.low,
                    abs(candle.high - previous_close),
                    abs(candle.low - previous_close),
                )
            )
        previous_close = candle.close
    return ranges


def _atr(candles: list[OhlcvCandle], period: int = 14) -> float:
    if not candles:
        return 0.0
    ranges = _true_ranges(candles)
    return _avg(ranges[-period:], candles[-1].close * 0.02)


def _linear_regression_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x_mean = (len(values) - 1) / 2
    y_mean = mean(values)
    numerator = sum(
        (idx - x_mean) * (value - y_mean) for idx, value in enumerate(values)
    )
    denominator = sum((idx - x_mean) ** 2 for idx in range(len(values)))
    return numerator / denominator if denominator else 0.0


def _safe_pct(numerator: float, denominator: float) -> float:
    return numerator / denominator * 100 if denominator else 0.0


def _sma(values: list[float], period: int) -> float:
    if not values:
        return 0.0
    return _avg(values[-period:], values[-1])


def _recent_swing_low(candles: list[OhlcvCandle], window: int = 10) -> float:
    if not candles:
        return 0.0
    return min(candle.low for candle in candles[-window:])


def find_price_levels(
    candles: list[OhlcvCandle], config: BacktestConfig
) -> tuple[list[PriceLevel], list[PriceLevel]]:
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    if len(ordered) < config.swing_window * 2 + 1:
        return [], []

    tolerance = config.level_tolerance_pct
    avg_volume = _avg(
        [candle.volume for candle in ordered[-config.volume_period :]], 1.0
    )
    support_candidates: list[tuple[float, int, float]] = []
    resistance_candidates: list[tuple[float, int, float]] = []
    window = config.swing_window

    for idx in range(window, len(ordered) - window):
        segment = ordered[idx - window : idx + window + 1]
        candle = ordered[idx]
        volume_ratio = candle.volume / avg_volume if avg_volume > 0 else 1.0
        if candle.low <= min(item.low for item in segment):
            support_candidates.append((candle.low, idx, volume_ratio))
        if candle.high >= max(item.high for item in segment):
            resistance_candidates.append((candle.high, idx, volume_ratio))

    def cluster(
        candidates: list[tuple[float, int, float]], kind: str
    ) -> list[PriceLevel]:
        clusters: list[list[tuple[float, int, float]]] = []
        for candidate in sorted(candidates, key=lambda item: item[0]):
            price = candidate[0]
            for group in clusters:
                base = _avg([item[0] for item in group])
                if base and abs(price - base) / base <= tolerance:
                    group.append(candidate)
                    break
            else:
                clusters.append([candidate])

        levels: list[PriceLevel] = []
        latest_idx = len(ordered) - 1
        for group in clusters:
            touches = len(group)
            price = _avg([item[0] for item in group])
            last_idx = max(item[1] for item in group)
            recency = 1.0 - min((latest_idx - last_idx) / max(len(ordered), 1), 1.0)
            volume_score = min(_avg([item[2] for item in group]) / 2.0, 1.0)
            touch_score = min(touches / 5.0, 1.0)
            strength = round(
                (touch_score * 0.45) + (recency * 0.35) + (volume_score * 0.2), 4
            )
            levels.append(
                PriceLevel(
                    price=_round_money(price),
                    kind=kind,  # type: ignore[arg-type]
                    strength=strength,
                    touches=touches,
                    last_touched_at=ordered[last_idx].timestamp,
                )
            )
        return sorted(
            levels, key=lambda level: (level.strength, level.touches), reverse=True
        )

    return cluster(support_candidates, "support"), cluster(
        resistance_candidates, "resistance"
    )


def _nearest_support(levels: list[PriceLevel], price: float) -> PriceLevel | None:
    supports = [level for level in levels if level.price <= price]
    return max(supports, key=lambda level: level.price, default=None)


def _nearest_resistance(levels: list[PriceLevel], price: float) -> PriceLevel | None:
    resistances = [level for level in levels if level.price >= price]
    return min(resistances, key=lambda level: level.price, default=None)


def _crossed_resistance(
    levels: list[PriceLevel],
    previous_close: float,
    current_close: float,
    buffer_pct: float,
) -> PriceLevel | None:
    crossed = [
        level
        for level in levels
        if previous_close <= level.price
        and current_close > level.price * (1 + buffer_pct)
    ]
    return max(crossed, key=lambda level: (level.price, level.strength), default=None)


def _calculate_metrics(
    *,
    initial_capital: float,
    final_capital: float,
    trades: list[BacktestTrade],
    equity_curve: list[EquityPoint],
) -> BacktestMetrics:
    peak = initial_capital
    max_drawdown = 0.0
    returns: list[float] = []
    previous_equity = initial_capital

    for point in equity_curve:
        peak = max(peak, point.equity)
        if peak > 0:
            max_drawdown = min(max_drawdown, (point.equity - peak) / peak)
        if previous_equity > 0:
            returns.append((point.equity / previous_equity) - 1.0)
        previous_equity = point.equity

    closed = [trade for trade in trades if trade.pnl is not None]
    wins = [trade.pnl or 0.0 for trade in closed if (trade.pnl or 0.0) > 0]
    losses = [trade.pnl or 0.0 for trade in closed if (trade.pnl or 0.0) < 0]
    profit_factor = (
        sum(wins) / abs(sum(losses)) if losses else (sum(wins) if wins else 0.0)
    )
    sharpe = 0.0
    if len(returns) > 1:
        stdev = pstdev(returns)
        sharpe = (mean(returns) / stdev * sqrt(252)) if stdev else 0.0

    return BacktestMetrics(
        initial_capital=_round_money(initial_capital),
        final_capital=_round_money(final_capital),
        total_return_pct=round(
            _safe_pct(final_capital - initial_capital, initial_capital), 4
        ),
        max_drawdown_pct=round(max_drawdown * 100, 4),
        trade_count=len(closed),
        win_rate_pct=round(_safe_pct(len(wins), len(closed)), 4),
        profit_factor=round(profit_factor, 4),
        sharpe_ratio=round(sharpe, 4),
    )


def run_support_resistance_backtest(
    *,
    symbol: str,
    candles: list[OhlcvCandle],
    config: BacktestConfig,
    symbol_name: str | None = None,
    avg_trade_amount: float | None = None,
    trade_start_date: date | None = None,
) -> BacktestResponse:
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    minimum_history = (
        max(config.lookback_period, config.slope_period, config.volume_period)
        + config.swing_window * 2
    )
    if len(ordered) <= minimum_history + 1:
        raise ValueError(
            f"백테스트에는 최소 {minimum_history + 2}개의 캔들이 필요합니다."
        )

    cash = config.initial_capital
    quantity = 0
    open_trade: BacktestTrade | None = None
    open_trade_cost = 0.0
    trades: list[BacktestTrade] = []
    equity_curve: list[EquityPoint] = []
    notes: list[str] = [
        "신호는 해당 캔들 종가 기준으로 계산하고 다음 캔들 시가에 체결한 것으로 가정합니다.",
        "KIS 실거래 체결가, 호가 잔량, 부분 체결은 반영하지 않은 단순 백테스트입니다.",
    ]

    for idx in range(minimum_history, len(ordered) - 1):
        history = ordered[max(0, idx - config.lookback_period + 1) : idx + 1]
        candle = ordered[idx]
        previous = ordered[idx - 1]
        next_candle = ordered[idx + 1]

        supports, resistances = find_price_levels(history, config)
        support = _nearest_support(supports, candle.close)
        recent_closes = [
            item.close for item in ordered[idx - config.slope_period + 1 : idx + 1]
        ]
        atr = _atr(history)
        slope_atr = _linear_regression_slope(recent_closes) / atr if atr > 0 else 0.0
        avg_volume = _avg(
            [item.volume for item in ordered[idx - config.volume_period + 1 : idx + 1]],
            1.0,
        )
        volume_ratio = candle.volume / avg_volume if avg_volume > 0 else 1.0
        is_in_trade_period = (
            trade_start_date is None or candle.timestamp.date() >= trade_start_date
        )

        if is_in_trade_period and quantity > 0 and open_trade is not None:
            exit_reason: str | None = None
            if candle.close <= open_trade.stop_loss:
                exit_reason = "stop_loss"
            elif candle.close >= open_trade.take_profit:
                exit_reason = "take_profit"
            elif slope_atr < -abs(config.min_slope_atr):
                exit_reason = "slope_reversal"
            elif (
                support
                and candle.close < support.price * (1 - config.stop_loss_buffer_pct)
                and volume_ratio >= config.min_volume_ratio
            ):
                exit_reason = "support_breakdown"

            if exit_reason:
                sell_price = next_candle.open * (1 - config.slippage_pct)
                gross = quantity * sell_price
                fee = gross * (config.commission_rate + config.tax_rate)
                net = gross - fee
                cash += net
                open_trade.exit_at = next_candle.timestamp
                open_trade.exit_price = _round_money(sell_price)
                open_trade.exit_reason = exit_reason
                open_trade.pnl = _round_money(net - open_trade_cost)
                open_trade.pnl_pct = round(
                    _safe_pct(net - open_trade_cost, open_trade_cost), 4
                )
                quantity = 0
                open_trade = None
                open_trade_cost = 0.0

        if is_in_trade_period and quantity == 0:
            crossed_resistance = _crossed_resistance(
                resistances,
                previous.close,
                candle.close,
                config.breakout_buffer_pct,
            )
            breakout = (
                crossed_resistance is not None
                and volume_ratio >= config.min_volume_ratio
                and slope_atr >= config.min_slope_atr
            )
            bounce = (
                support is not None
                and candle.low <= support.price * (1 + config.level_tolerance_pct)
                and candle.close > support.price * (1 + config.breakout_buffer_pct)
                and candle.close > candle.open
                and volume_ratio >= config.min_volume_ratio
                and slope_atr >= -abs(config.min_slope_atr)
            )

            if breakout or bounce:
                buy_price = next_candle.open * (1 + config.slippage_pct)
                budget = cash * config.position_size_pct
                quantity_to_buy = int(budget // buy_price)
                if quantity_to_buy > 0:
                    entry_value = quantity_to_buy * buy_price
                    entry_fee = entry_value * config.commission_rate
                    cash -= entry_value + entry_fee
                    quantity = quantity_to_buy

                    if support is not None:
                        stop_loss = support.price * (1 - config.stop_loss_buffer_pct)
                    else:
                        stop_loss = buy_price - (_atr(history) * 1.5)

                    risk = max(buy_price - stop_loss, buy_price * 0.01)
                    next_resistance = _nearest_resistance(
                        resistances, candle.close * (1 + config.breakout_buffer_pct)
                    )
                    candidate_take_profit = (
                        next_resistance.price
                        if next_resistance and next_resistance.price > buy_price
                        else 0.0
                    )
                    take_profit = max(
                        candidate_take_profit,
                        buy_price + risk * config.risk_reward_ratio,
                    )

                    trade = BacktestTrade(
                        entry_at=next_candle.timestamp,
                        entry_price=_round_money(buy_price),
                        quantity=quantity,
                        reason="resistance_breakout" if breakout else "support_bounce",
                        stop_loss=_round_money(stop_loss),
                        take_profit=_round_money(take_profit),
                    )
                    trades.append(trade)
                    open_trade = trade
                    open_trade_cost = entry_value + entry_fee

        if is_in_trade_period:
            position_value = quantity * candle.close
            equity_curve.append(
                EquityPoint(
                    timestamp=candle.timestamp,
                    equity=_round_money(cash + position_value),
                    cash=_round_money(cash),
                    position_value=_round_money(position_value),
                    close=_round_money(candle.close),
                )
            )

    last_candle = ordered[-1]
    if quantity > 0 and open_trade is not None:
        sell_price = last_candle.close * (1 - config.slippage_pct)
        gross = quantity * sell_price
        fee = gross * (config.commission_rate + config.tax_rate)
        net = gross - fee
        cash += net
        open_trade.exit_at = last_candle.timestamp
        open_trade.exit_price = _round_money(sell_price)
        open_trade.exit_reason = "end_of_data"
        open_trade.pnl = _round_money(net - open_trade_cost)
        open_trade.pnl_pct = round(_safe_pct(net - open_trade_cost, open_trade_cost), 4)
        quantity = 0

    final_capital = cash + quantity * last_candle.close
    final_supports, final_resistances = find_price_levels(
        ordered[-config.lookback_period :], config
    )
    metrics = _calculate_metrics(
        initial_capital=config.initial_capital,
        final_capital=final_capital,
        trades=trades,
        equity_curve=equity_curve,
    )

    return BacktestResponse(
        symbol=symbol,
        symbol_name=symbol_name,
        avg_trade_amount=(
            _round_money(avg_trade_amount) if avg_trade_amount is not None else None
        ),
        metrics=metrics,
        supports=final_supports[:5],
        resistances=final_resistances[:5],
        trades=trades,
        equity_curve=equity_curve,
        notes=notes,
    )


def run_pullback_rebound_backtest(
    *,
    symbol: str,
    candles: list[OhlcvCandle],
    config: BacktestConfig,
    symbol_name: str | None = None,
    avg_trade_amount: float | None = None,
    trade_start_date: date | None = None,
) -> BacktestResponse:
    ordered = sorted(candles, key=lambda candle: candle.timestamp)
    short_ma_period = 20
    long_ma_period = 60
    pullback_window = 20
    minimum_history = max(long_ma_period, config.volume_period, config.slope_period) + 2
    if len(ordered) <= minimum_history + 1:
        raise ValueError(
            f"백테스트에는 최소 {minimum_history + 2}개의 캔들이 필요합니다."
        )

    cash = config.initial_capital
    quantity = 0
    open_trade: BacktestTrade | None = None
    open_trade_cost = 0.0
    trades: list[BacktestTrade] = []
    equity_curve: list[EquityPoint] = []
    notes: list[str] = [
        "공통 종목군에서 상승 추세 속 눌림 이후 반등 신호만 추적합니다.",
        "진입은 반등 신호 다음 캔들 시가, 청산은 손절/추세훼손/목표가 기준입니다.",
    ]

    for idx in range(minimum_history, len(ordered) - 1):
        candle = ordered[idx]
        previous = ordered[idx - 1]
        next_candle = ordered[idx + 1]
        history = ordered[: idx + 1]
        trade_history = ordered[max(0, idx - pullback_window + 1) : idx + 1]
        recent_closes = [
            item.close for item in ordered[idx - config.slope_period + 1 : idx + 1]
        ]
        recent_high = max(item.high for item in trade_history)
        closes = [item.close for item in history]
        short_ma = _sma(closes, short_ma_period)
        long_ma = _sma(closes, long_ma_period)
        atr = _atr(history)
        slope_atr = _linear_regression_slope(recent_closes) / atr if atr > 0 else 0.0
        avg_volume = _avg(
            [item.volume for item in ordered[idx - config.volume_period + 1 : idx + 1]],
            1.0,
        )
        volume_ratio = candle.volume / avg_volume if avg_volume > 0 else 1.0
        supports, resistances = find_price_levels(
            ordered[max(0, idx - config.lookback_period + 1) : idx + 1], config
        )
        support = _nearest_support(supports, candle.close)
        is_in_trade_period = (
            trade_start_date is None or candle.timestamp.date() >= trade_start_date
        )

        if is_in_trade_period and quantity > 0 and open_trade is not None:
            exit_reason: str | None = None
            if candle.close <= open_trade.stop_loss:
                exit_reason = "stop_loss"
            elif candle.close >= open_trade.take_profit:
                exit_reason = "take_profit"
            elif candle.close < short_ma:
                exit_reason = "short_ma_break"
            elif slope_atr < -abs(config.min_slope_atr):
                exit_reason = "trend_break"

            if exit_reason:
                sell_price = next_candle.open * (1 - config.slippage_pct)
                gross = quantity * sell_price
                fee = gross * (config.commission_rate + config.tax_rate)
                net = gross - fee
                cash += net
                open_trade.exit_at = next_candle.timestamp
                open_trade.exit_price = _round_money(sell_price)
                open_trade.exit_reason = exit_reason
                open_trade.pnl = _round_money(net - open_trade_cost)
                open_trade.pnl_pct = round(
                    _safe_pct(net - open_trade_cost, open_trade_cost), 4
                )
                quantity = 0
                open_trade = None
                open_trade_cost = 0.0

        if is_in_trade_period and quantity == 0:
            pullback_pct = (
                (recent_high - candle.close) / recent_high if recent_high > 0 else 0.0
            )
            short_ma_gap_pct = (
                abs(candle.close - short_ma) / short_ma if short_ma > 0 else 0.0
            )
            uptrend = (
                candle.close > long_ma
                and short_ma > long_ma
                and slope_atr >= max(config.min_slope_atr, 0.0)
            )
            pullback = 0.02 <= pullback_pct <= 0.12
            near_support = support is not None and candle.low <= support.price * (
                1 + config.level_tolerance_pct
            )
            near_short_ma = (
                short_ma > 0
                and short_ma_gap_pct <= 0.03
                and candle.low <= short_ma * (1 + config.level_tolerance_pct)
            )
            rebound = (
                candle.close > candle.open
                and candle.close > previous.close
                and volume_ratio >= max(1.0, config.min_volume_ratio * 0.85)
            )

            if uptrend and pullback and rebound and (near_support or near_short_ma):
                buy_price = next_candle.open * (1 + config.slippage_pct)
                budget = cash * config.position_size_pct
                quantity_to_buy = int(budget // buy_price)
                if quantity_to_buy > 0:
                    entry_value = quantity_to_buy * buy_price
                    entry_fee = entry_value * config.commission_rate
                    cash -= entry_value + entry_fee
                    quantity = quantity_to_buy

                    swing_low = _recent_swing_low(trade_history, window=10)
                    support_price = support.price if support is not None else swing_low
                    stop_loss = min(swing_low, support_price) * (
                        1 - config.stop_loss_buffer_pct
                    )
                    risk = max(buy_price - stop_loss, buy_price * 0.01)
                    next_resistance = _nearest_resistance(resistances, buy_price)
                    candidate_take_profit = (
                        next_resistance.price
                        if next_resistance and next_resistance.price > buy_price
                        else recent_high
                    )
                    take_profit = max(
                        candidate_take_profit,
                        buy_price + risk * config.risk_reward_ratio,
                    )

                    trade = BacktestTrade(
                        entry_at=next_candle.timestamp,
                        entry_price=_round_money(buy_price),
                        quantity=quantity,
                        reason="pullback_rebound",
                        stop_loss=_round_money(stop_loss),
                        take_profit=_round_money(take_profit),
                    )
                    trades.append(trade)
                    open_trade = trade
                    open_trade_cost = entry_value + entry_fee

        if is_in_trade_period:
            position_value = quantity * candle.close
            equity_curve.append(
                EquityPoint(
                    timestamp=candle.timestamp,
                    equity=_round_money(cash + position_value),
                    cash=_round_money(cash),
                    position_value=_round_money(position_value),
                    close=_round_money(candle.close),
                )
            )

    last_candle = ordered[-1]
    if quantity > 0 and open_trade is not None:
        sell_price = last_candle.close * (1 - config.slippage_pct)
        gross = quantity * sell_price
        fee = gross * (config.commission_rate + config.tax_rate)
        net = gross - fee
        cash += net
        open_trade.exit_at = last_candle.timestamp
        open_trade.exit_price = _round_money(sell_price)
        open_trade.exit_reason = "end_of_data"
        open_trade.pnl = _round_money(net - open_trade_cost)
        open_trade.pnl_pct = round(_safe_pct(net - open_trade_cost, open_trade_cost), 4)
        quantity = 0

    final_capital = cash + quantity * last_candle.close
    final_supports, final_resistances = find_price_levels(
        ordered[-config.lookback_period :], config
    )
    metrics = _calculate_metrics(
        initial_capital=config.initial_capital,
        final_capital=final_capital,
        trades=trades,
        equity_curve=equity_curve,
    )

    return BacktestResponse(
        symbol=symbol,
        symbol_name=symbol_name,
        avg_trade_amount=(
            _round_money(avg_trade_amount) if avg_trade_amount is not None else None
        ),
        metrics=metrics,
        supports=final_supports[:5],
        resistances=final_resistances[:5],
        trades=trades,
        equity_curve=equity_curve,
        notes=notes,
    )
