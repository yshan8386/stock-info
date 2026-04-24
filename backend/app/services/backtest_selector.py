from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import sin, sqrt, tau
from statistics import mean, pstdev
from typing import Any

from app.schemas.backtest import (
    AutoBacktestRequest,
    AutoBacktestResponse,
    BacktestConfig,
    BacktestResponse,
    EquityPoint,
    OhlcvCandle,
    StockSelectionItem,
    StrategyBacktestRun,
    StrategyComparisonSummary,
)
from app.services.backtest_strategies import get_strategy_definition

_POSITION_SIZE_PCT = 0.95

# 백테스트 엔진 warmup 기간 (일봉 기준 — minimum_history 기본값보다 넉넉하게)
_WARMUP_MARKET_DAYS = 100
_WARMUP_CALENDAR_DAYS = int(_WARMUP_MARKET_DAYS * 7 / 5) + 30  # 시장일 → 달력일 변환

# (종목코드, 이름, 일평균거래대금, 기준가, 추세, 변동성, 시가총액)
# KIS 키가 없을 때 사용하는 목업 후보 (시가총액 단위: 원)
_MOCK_CANDIDATES = [
    ("005930", "삼성전자", 18_000_000_000, 73_000, 0.24, 0.9, 400_000_000_000_000),
    ("000660", "SK하이닉스", 14_500_000_000, 172_000, 0.31, 1.1, 105_000_000_000_000),
    ("005380", "현대차", 9_200_000_000, 241_000, 0.19, 0.8, 52_000_000_000_000),
    ("035420", "NAVER", 7_800_000_000, 188_000, 0.14, 0.7, 29_000_000_000_000),
    (
        "207940",
        "삼성바이오로직스",
        3_600_000_000,
        810_000,
        0.04,
        0.45,
        48_000_000_000_000,
    ),
    ("035720", "카카오", 6_600_000_000, 49_000, 0.12, 0.6, 21_000_000_000_000),
    ("068270", "셀트리온", 4_800_000_000, 184_000, 0.09, 0.55, 24_000_000_000_000),
    ("051910", "LG화학", 5_900_000_000, 362_000, -0.03, 0.5, 19_000_000_000_000),
]


@dataclass
class UniverseCandidate:
    item: StockSelectionItem
    candles: list[OhlcvCandle]
    previous_day_volume: float


def _avg(values: list[float], default: float = 0.0) -> float:
    return mean(values) if values else default


def _safe_pct(numerator: float, denominator: float) -> float:
    return numerator / denominator * 100 if denominator else 0.0


def _make_kis_client() -> Any | None:
    """KIS 설정이 있으면 싱글톤 클라이언트를 반환하고, 없으면 None을 반환한다."""
    try:
        from app.config import get_settings
        from app.services.kis_client import get_client

        settings = get_settings()
        if not settings.kis_configured:
            return None
        return get_client(
            app_key=settings.kis_app_key,  # type: ignore[arg-type]
            app_secret=settings.kis_app_secret,  # type: ignore[arg-type]
            base_url=settings.kis_base_url,
        )
    except Exception:
        return None


def _ohlcv_rows_to_candles(rows: list[dict[str, Any]]) -> list[OhlcvCandle]:
    candles: list[OhlcvCandle] = []
    for row in rows:
        try:
            ts = datetime.strptime(row["date"], "%Y%m%d")
            o, h, l, c = row["open"], row["high"], row["low"], row["close"]
            volume = row["volume"]
            if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                continue
            if h < max(o, c) or l > min(o, c):
                continue
            candles.append(
                OhlcvCandle(timestamp=ts, open=o, high=h, low=l, close=c, volume=volume)
            )
        except Exception:
            continue
    return candles


def _market_days(start_date: date, end_date: date) -> list[date]:
    days: list[date] = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _generate_mock_candles(
    *,
    symbol_index: int,
    start_date: date,
    end_date: date,
    base_price: float,
    trend: float,
    volatility: float,
    base_trade_amount: float,
) -> list[OhlcvCandle]:
    warmup_start = start_date - timedelta(days=180)
    days = _market_days(warmup_start, end_date)
    candles: list[OhlcvCandle] = []
    price = base_price

    for idx, day in enumerate(days):
        cycle = sin((idx + symbol_index * 3) / 14 * tau)
        secondary = sin((idx + symbol_index) / 39 * tau)
        drift = trend * idx / max(len(days), 1)
        price = max(
            base_price * 0.35,
            base_price
            * (1 + drift + volatility * 0.035 * cycle + volatility * 0.018 * secondary),
        )
        if idx > len(days) * 0.72 and trend > 0:
            price *= 1 + (idx - len(days) * 0.72) / len(days) * trend * 0.8

        open_price = price * (1 - 0.004 * cycle)
        high = max(open_price, price) * (1 + 0.009 + abs(cycle) * 0.006)
        low = min(open_price, price) * (1 - 0.009 - abs(secondary) * 0.005)
        trade_amount = base_trade_amount * (
            1 + abs(cycle) * 0.28 + max(trend, 0) * 0.15
        )
        volume = max(1, int(trade_amount / max(price, 1)))

        candles.append(
            OhlcvCandle(
                timestamp=datetime.combine(day, datetime.min.time()),
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(price, 2),
                volume=volume,
            )
        )
    return candles


def _build_candidate(
    *,
    symbol: str,
    name: str,
    candles: list[OhlcvCandle],
    market_cap: float | None,
    planned_position_budget: float,
    selection_cutoff: date,
) -> UniverseCandidate | None:
    selection_candles = [
        candle for candle in candles if candle.timestamp.date() < selection_cutoff
    ]
    if not selection_candles:
        return None

    selection_candle = selection_candles[-1]
    recent = (
        selection_candles[-20:] if len(selection_candles) >= 20 else selection_candles
    )
    avg_trade_amount = sum(candle.close * candle.volume for candle in recent) / max(
        len(recent), 1
    )
    planned_qty = int(planned_position_budget // selection_candle.close)
    if planned_qty < 1:
        return None

    return UniverseCandidate(
        item=StockSelectionItem(
            symbol=symbol,
            name=name,
            avg_trade_amount=round(avg_trade_amount, 2),
            current_price=float(selection_candle.close),
            market_cap=float(market_cap) if market_cap is not None else None,
            allocated_budget=0.0,
            max_buyable_quantity=planned_qty,
            score=0.0,
            reason="",
        ),
        candles=candles,
        previous_day_volume=float(selection_candle.volume),
    )


def _rank_candidates(
    candidates: list[UniverseCandidate], max_symbols: int
) -> list[UniverseCandidate]:
    market_cap_order = sorted(
        candidates,
        key=lambda candidate: (
            candidate.item.market_cap or 0.0,
            candidate.previous_day_volume,
        ),
        reverse=True,
    )
    volume_order = sorted(
        candidates,
        key=lambda candidate: (
            candidate.previous_day_volume,
            candidate.item.market_cap or 0.0,
        ),
        reverse=True,
    )
    market_cap_rank = {
        candidate.item.symbol: index + 1
        for index, candidate in enumerate(market_cap_order)
    }
    volume_rank = {
        candidate.item.symbol: index + 1 for index, candidate in enumerate(volume_order)
    }
    universe_size = len(candidates)

    for candidate in candidates:
        symbol = candidate.item.symbol
        cap_rank = market_cap_rank[symbol]
        vol_rank = volume_rank[symbol]
        cap_score = ((universe_size - cap_rank + 1) / universe_size) * 50
        vol_score = ((universe_size - vol_rank + 1) / universe_size) * 50
        candidate.item.score = round(cap_score + vol_score, 2)
        candidate.item.reason = f"시총 {cap_rank}위 · 전일 거래량 {vol_rank}위"

    ranked = sorted(
        candidates,
        key=lambda candidate: (
            candidate.item.score,
            candidate.item.market_cap or 0.0,
            candidate.previous_day_volume,
        ),
        reverse=True,
    )
    return ranked[:max_symbols]


def _merge_equity_curves(results: list[BacktestResponse]) -> list[EquityPoint]:
    merged: dict[datetime, dict[str, float]] = {}
    for result in results:
        for point in result.equity_curve:
            bucket = merged.setdefault(
                point.timestamp,
                {"equity": 0.0, "cash": 0.0, "position_value": 0.0, "close": 0.0},
            )
            bucket["equity"] += point.equity
            bucket["cash"] += point.cash
            bucket["position_value"] += point.position_value
            bucket["close"] += point.close

    return [
        EquityPoint(
            timestamp=timestamp,
            equity=round(values["equity"], 2),
            cash=round(values["cash"], 2),
            position_value=round(values["position_value"], 2),
            close=round(values["close"], 2),
        )
        for timestamp, values in sorted(merged.items())
    ]


def _summarize_strategy(
    strategy_id: str, strategy_label: str, results: list[BacktestResponse]
) -> StrategyComparisonSummary:
    equity_curve = _merge_equity_curves(results)
    initial_capital = sum(result.metrics.initial_capital for result in results)
    final_capital = sum(result.metrics.final_capital for result in results)
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

    closed_trades = [
        trade for result in results for trade in result.trades if trade.pnl is not None
    ]
    wins = [trade for trade in closed_trades if (trade.pnl or 0.0) > 0]
    sharpe_ratio = 0.0
    if len(returns) > 1:
        stdev = pstdev(returns)
        sharpe_ratio = (mean(returns) / stdev * sqrt(252)) if stdev else 0.0

    return StrategyComparisonSummary(
        strategy_id=strategy_id,
        strategy_label=strategy_label,
        initial_capital=round(initial_capital, 2),
        final_capital=round(final_capital, 2),
        total_return_pct=round(
            _safe_pct(final_capital - initial_capital, initial_capital), 4
        ),
        max_drawdown_pct=round(max_drawdown * 100, 4),
        trade_count=len(closed_trades),
        win_rate_pct=round(_safe_pct(len(wins), len(closed_trades)), 4),
        sharpe_ratio=round(sharpe_ratio, 4),
    )


def _execute_strategies(
    request: AutoBacktestRequest, selected: list[UniverseCandidate]
) -> list[StrategyBacktestRun]:
    if not selected:
        return []

    strategy_runs: list[StrategyBacktestRun] = []
    capital_per_symbol = request.initial_capital / max(len(selected), 1)
    for candidate in selected:
        candidate.item.allocated_budget = round(capital_per_symbol, 2)
        candidate.item.max_buyable_quantity = int(
            (capital_per_symbol * _POSITION_SIZE_PCT) // candidate.item.current_price
        )

    for strategy_id in request.strategy_ids:
        strategy = get_strategy_definition(strategy_id)
        results: list[BacktestResponse] = []

        for candidate in selected:
            windowed = [
                candle
                for candle in candidate.candles
                if candle.timestamp.date() <= request.end_date
            ]
            try:
                result = strategy.runner(
                    symbol=candidate.item.symbol,
                    symbol_name=candidate.item.name,
                    avg_trade_amount=candidate.item.avg_trade_amount,
                    candles=windowed,
                    config=BacktestConfig(
                        initial_capital=capital_per_symbol,
                        position_size_pct=_POSITION_SIZE_PCT,
                        min_volume_ratio=1.03,
                        min_slope_atr=0.0,
                    ),
                    trade_start_date=request.start_date,
                )
            except ValueError:
                continue
            results.append(result)

        strategy_runs.append(
            StrategyBacktestRun(
                strategy=strategy.info,
                summary=_summarize_strategy(
                    strategy.info.id, strategy.info.label, results
                ),
                results=results,
            )
        )

    return strategy_runs


def _build_response(
    request: AutoBacktestRequest,
    selected: list[UniverseCandidate],
    *,
    notes: list[str],
) -> AutoBacktestResponse:
    strategy_runs = _execute_strategies(request, selected)
    primary_results = strategy_runs[0].results if strategy_runs else []
    return AutoBacktestResponse(
        request=request,
        selected=[candidate.item for candidate in selected],
        strategy_runs=strategy_runs,
        results=primary_results,
        notes=notes,
    )


def _run_real_data_backtest(
    request: AutoBacktestRequest,
) -> AutoBacktestResponse | None:
    client = _make_kis_client()
    if client is None:
        return None

    try:
        rank_items = client.get_trade_amount_rank(count=120)
    except Exception:
        return None

    if not rank_items:
        return None

    warmup_start = request.start_date - timedelta(days=_WARMUP_CALENDAR_DAYS)
    planned_budget = request.initial_capital / max(request.max_symbols, 1)
    planned_position_budget = planned_budget * _POSITION_SIZE_PCT
    generated: list[UniverseCandidate] = []
    excluded_by_price = 0

    for rank_item in rank_items:
        symbol = rank_item["code"]
        try:
            rows = client.get_daily_ohlcv(symbol, warmup_start, request.end_date)
        except Exception:
            continue

        candles = _ohlcv_rows_to_candles(rows)
        if len(candles) < 80:
            continue

        period_candles = [
            candle for candle in candles if candle.timestamp.date() <= request.end_date
        ]
        if len(period_candles) < 80:
            continue

        candidate = _build_candidate(
            symbol=symbol,
            name=rank_item["name"],
            candles=period_candles,
            market_cap=(
                float(rank_item["market_cap"]) if rank_item["market_cap"] else None
            ),
            planned_position_budget=planned_position_budget,
            selection_cutoff=request.start_date,
        )
        if candidate is None:
            excluded_by_price += 1
            continue
        generated.append(candidate)

    selected = _rank_candidates(generated, request.max_symbols)
    notes = [
        "KIS OpenAPI 실데이터 기반 공통 종목선정 + 전략 비교 백테스트입니다.",
        "후보 풀은 KIS 유동성 상위 종목에서 만들고, 실제 선택은 시가총액과 전일 거래량 종합 순위로 정렬합니다.",
        f"전략 비교 대상: {', '.join(request.strategy_ids)}",
    ]
    if excluded_by_price:
        notes.append(
            f"종목당 예산으로 1주도 살 수 없는 후보 {excluded_by_price}개는 제외했습니다."
        )
    if not selected:
        notes.append(
            "조건을 통과한 후보가 없습니다. 초기 자본을 늘리거나 후보 풀을 넓혀야 합니다."
        )

    return _build_response(request, selected, notes=notes)


def _run_mock_backtest(request: AutoBacktestRequest) -> AutoBacktestResponse:
    planned_budget = request.initial_capital / max(request.max_symbols, 1)
    planned_position_budget = planned_budget * _POSITION_SIZE_PCT
    generated: list[UniverseCandidate] = []
    excluded_by_price = 0

    for index, (
        symbol,
        name,
        base_trade_amount,
        base_price,
        trend,
        volatility,
        market_cap,
    ) in enumerate(_MOCK_CANDIDATES):
        candles = _generate_mock_candles(
            symbol_index=index,
            start_date=request.start_date,
            end_date=request.end_date,
            base_price=base_price,
            trend=trend,
            volatility=volatility,
            base_trade_amount=base_trade_amount,
        )
        candidate = _build_candidate(
            symbol=symbol,
            name=name,
            candles=candles,
            market_cap=float(market_cap),
            planned_position_budget=planned_position_budget,
            selection_cutoff=request.start_date,
        )
        if candidate is None:
            excluded_by_price += 1
            continue
        generated.append(candidate)

    selected = _rank_candidates(generated, request.max_symbols)
    notes = [
        "[목업 모드] KIS_APP_KEY / KIS_APP_SECRET 환경변수가 없어 내장 가상 OHLCV로 동작합니다.",
        "실제 종목선정·전략 비교 결과를 얻으려면 .env에 KIS OpenAPI 키를 설정하세요.",
        "공통 종목선정은 시가총액과 전일 거래량 종합 순위입니다.",
        f"전략 비교 대상: {', '.join(request.strategy_ids)}",
    ]
    if excluded_by_price:
        notes.append(
            f"종목당 예산으로 1주도 살 수 없는 후보 {excluded_by_price}개는 제외했습니다."
        )
    if not selected:
        notes.append(
            "조건을 통과한 후보가 없습니다. 초기 자본을 늘리거나 후보 풀을 넓혀야 합니다."
        )

    return _build_response(request, selected, notes=notes)


def run_auto_backtest(request: AutoBacktestRequest) -> AutoBacktestResponse:
    real_result = _run_real_data_backtest(request)
    if real_result is not None:
        return real_result
    return _run_mock_backtest(request)
