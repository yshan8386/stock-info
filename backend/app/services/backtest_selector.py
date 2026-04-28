from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import sqrt
from statistics import mean, pstdev
from typing import Any

from bs4 import BeautifulSoup

from app.schemas.backtest import (
    AutoBacktestRequest,
    AutoBacktestResponse,
    BacktestConfig,
    BenchmarkPoint,
    BacktestResponse,
    EquityPoint,
    OhlcvCandle,
    SelectedSymbol,
    StockDetailCandle,
    StockDetailResponse,
    StockSearchItem,
    StockSelectionDateResult,
    StockSelectionItem,
    StockSelectionRangeRequest,
    StockSelectionRangeResponse,
    StockSelectionRequest,
    StockSelectionResponse,
    StrategyBacktestRun,
    StrategyComparisonSummary,
    StrategyOnlyRequest,
    StrategyRunsResponse,
)
from app.services.kis_stock_master import search_stock_master
from app.services.backtest_strategies import get_strategy_definition

_POSITION_SIZE_PCT = 0.95
_WARMUP_MARKET_DAYS = 100
_WARMUP_CALENDAR_DAYS = int(_WARMUP_MARKET_DAYS * 7 / 5) + 30

_KNOWN_STOCKS: list[tuple[str, str]] = [
    ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("207940", "삼성바이오로직스"),
    ("005380", "현대차"), ("000270", "기아"), ("006400", "삼성SDI"),
    ("051910", "LG화학"), ("035420", "NAVER"), ("035720", "카카오"),
    ("068270", "셀트리온"), ("028260", "삼성물산"), ("012330", "현대모비스"),
    ("105560", "KB금융"), ("055550", "신한지주"), ("086790", "하나금융지주"),
    ("032830", "삼성생명"), ("003550", "LG"), ("096770", "SK이노베이션"),
    ("017670", "SK텔레콤"), ("030200", "KT"), ("066570", "LG전자"),
    ("015760", "한국전력"), ("090430", "아모레퍼시픽"),
    ("034730", "SK"), ("316140", "우리금융지주"), ("024110", "기업은행"),
    ("033780", "KT&G"), ("009150", "삼성전기"), ("010950", "S-Oil"),
    ("005490", "POSCO홀딩스"), ("000810", "삼성화재"), ("010130", "고려아연"),
    ("086280", "현대글로비스"), ("034020", "두산에너빌리티"), ("042660", "한화오션"),
    ("009830", "한화솔루션"), ("138040", "메리츠금융지주"), ("003490", "대한항공"),
    ("011170", "롯데케미칼"), ("023530", "롯데쇼핑"), ("010140", "삼성중공업"),
    ("047040", "대우건설"),
    ("032640", "LG유플러스"), ("047050", "포스코인터내셔널"), ("028050", "삼성엔지니어링"),
    ("003620", "KCC"), ("004990", "롯데지주"), ("011790", "SKC"),
    ("018880", "한온시스템"), ("161390", "한국타이어앤테크놀로지"),
]
_OVERHEAT_LOOKBACK_DAYS = 20
_OVERHEAT_RETURN_LIMIT_PCT = 20.0
_NAVER_INDEX_DAY_URL = "https://finance.naver.com/sise/sise_index_day.naver"


@dataclass
class UniverseCandidate:
    item: StockSelectionItem
    candles: list[OhlcvCandle]
    recent_return_pct: float


@dataclass
class _StrategyExecutionContext:
    start_date: date
    end_date: date
    initial_capital: float
    max_positions: int
    strategy_ids: list[str]
    trend_filter: str = "none"
    rsi_min: float | None = None
    rsi_max: float | None = None
    min_volume_ratio: float | None = None


def _safe_pct(numerator: float, denominator: float) -> float:
    return numerator / denominator * 100 if denominator else 0.0


def _optional_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _get_kis_client() -> Any:
    try:
        from app.config import get_settings
        from app.services.kis_client import get_client

        settings = get_settings()
        if not settings.kis_configured:
            raise ValueError(
                "KIS OpenAPI 키가 설정되지 않았습니다. "
                ".env 파일에 KIS_APP_KEY, KIS_APP_SECRET을 설정하세요."
            )
        return get_client(
            app_key=settings.kis_app_key,  # type: ignore[arg-type]
            app_secret=settings.kis_app_secret,  # type: ignore[arg-type]
            base_url=settings.kis_base_url,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"KIS 클라이언트 초기화 실패: {exc}") from exc


def _ohlcv_rows_to_candles(rows: list[dict[str, Any]]) -> list[OhlcvCandle]:
    candles: list[OhlcvCandle] = []
    for row in rows:
        try:
            ts = datetime.strptime(row["date"], "%Y%m%d")
            open_, high, low, close, volume = (
                row["open"], row["high"], row["low"], row["close"], row["volume"],
            )
            if open_ <= 0 or high <= 0 or low <= 0 or close <= 0:
                continue
            if high < max(open_, close) or low > min(open_, close):
                continue
            candles.append(OhlcvCandle(
                timestamp=ts, open=open_, high=high, low=low, close=close, volume=volume,
            ))
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


_MA_TREND_WINDOW = 5
_MIN_CANDLES = 60 + _MA_TREND_WINDOW + 1


def _ma(closes: list[float], period: int, offset: int = 0) -> float:
    end = len(closes) - offset if offset > 0 else len(closes)
    return sum(closes[end - period : end]) / period


def _build_candidate(
    *,
    symbol: str,
    name: str,
    candles: list[OhlcvCandle],
    market_cap: float | None,
    selection_cutoff: date,
    price_cap: float,
) -> tuple[UniverseCandidate | None, str | None]:
    selection_candles = [c for c in candles if c.timestamp.date() < selection_cutoff]
    if len(selection_candles) < _MIN_CANDLES:
        return None, "이동평균 계산에 필요한 일봉 데이터가 부족해 제외"

    last = selection_candles[-1]
    closes = [c.close for c in selection_candles]

    if last.close > price_cap:
        return None, "주가가 초기 자본의 3분의 1을 초과해 제외"

    for period in (5, 20, 60):
        if _ma(closes, period) <= _ma(closes, period, _MA_TREND_WINDOW):
            return None, "5·20·60일선 상승 추세 조건을 만족하지 못해 제외"

    if last.volume < 2 * selection_candles[-2].volume:
        return None, "전일 대비 거래량 2배 증가 조건을 만족하지 못해 제외"

    if len(selection_candles) < _OVERHEAT_LOOKBACK_DAYS + 1:
        return None, "최근 20일 수익률 점검용 데이터가 부족해 제외"
    reference_candle = selection_candles[-(_OVERHEAT_LOOKBACK_DAYS + 1)]
    recent_return_pct = _safe_pct(last.close - reference_candle.close, reference_candle.close)
    if recent_return_pct > _OVERHEAT_RETURN_LIMIT_PCT:
        return None, f"최근 20일 수익률 {recent_return_pct:.1f}%로 과열 구간이라 제외"

    recent = selection_candles[-20:]
    avg_trade_amount = sum(c.close * c.volume for c in recent) / max(len(recent), 1)

    return UniverseCandidate(
        item=StockSelectionItem(
            symbol=symbol,
            name=name,
            avg_trade_amount=round(avg_trade_amount, 2),
            current_price=float(last.close),
            market_cap=float(market_cap) if market_cap is not None else None,
            allocated_budget=0.0,
            max_buyable_quantity=None,
            score=0.0,
            reason="",
        ),
        candles=candles,
        recent_return_pct=round(recent_return_pct, 2),
    ), None


def _rank_candidates(
    candidates: list[UniverseCandidate], max_symbols: int
) -> list[UniverseCandidate]:
    ranked = sorted(
        candidates,
        key=lambda c: (c.item.market_cap or 0.0, c.item.avg_trade_amount, -c.recent_return_pct),
        reverse=True,
    )
    for index, candidate in enumerate(ranked, start=1):
        candidate.item.score = round((candidate.item.market_cap or 0.0) / 1_000_000_000_000, 2)
        candidate.item.reason = (
            f"시총 {index}위권 · 최근 20일 수익률 {candidate.recent_return_pct:.1f}%"
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
            timestamp=ts,
            equity=round(v["equity"], 2),
            cash=round(v["cash"], 2),
            position_value=round(v["position_value"], 2),
            close=round(v["close"], 2),
        )
        for ts, v in sorted(merged.items())
    ]


def _fetch_kospi_benchmark_curve(
    start_date: date,
    end_date: date,
) -> list[BenchmarkPoint]:
    if start_date > end_date:
        return []

    try:
        import httpx
    except Exception:
        return []

    points: dict[date, BenchmarkPoint] = {}
    headers = {"user-agent": "Mozilla/5.0"}

    with httpx.Client(timeout=10, headers=headers, follow_redirects=True) as client:
        for page in range(1, 200):
            response = client.get(
                _NAVER_INDEX_DAY_URL,
                params={"code": "KOSPI", "page": str(page)},
            )
            response.raise_for_status()
            response.encoding = "euc-kr"
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("table.type_1 tr")
            page_dates: list[date] = []

            for row in rows:
                cells = [cell.get_text(strip=True) for cell in row.select("td")]
                if len(cells) < 2 or not cells[0] or not cells[1]:
                    continue
                try:
                    point_date = datetime.strptime(cells[0], "%Y.%m.%d").date()
                    close = float(cells[1].replace(",", ""))
                except ValueError:
                    continue

                page_dates.append(point_date)
                if start_date <= point_date <= end_date:
                    points[point_date] = BenchmarkPoint(
                        timestamp=datetime.combine(point_date, datetime.min.time()),
                        close=close,
                    )

            if not page_dates:
                break

            oldest_on_page = min(page_dates)
            if oldest_on_page <= start_date:
                break

    return [points[point_date] for point_date in sorted(points)]


def _summarize_strategy(
    strategy_id: str, strategy_label: str, results: list[BacktestResponse]
) -> StrategyComparisonSummary:
    equity_curve = _merge_equity_curves(results)
    initial_capital = sum(r.metrics.initial_capital for r in results)
    final_capital = sum(r.metrics.final_capital for r in results)
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

    closed_trades = [t for r in results for t in r.trades if t.pnl is not None]
    wins = [t for t in closed_trades if (t.pnl or 0.0) > 0]
    sharpe_ratio = 0.0
    if len(returns) > 1:
        stdev = pstdev(returns)
        sharpe_ratio = (mean(returns) / stdev * sqrt(252)) if stdev else 0.0

    return StrategyComparisonSummary(
        strategy_id=strategy_id,
        strategy_label=strategy_label,
        initial_capital=round(initial_capital, 2),
        final_capital=round(final_capital, 2),
        total_return_pct=round(_safe_pct(final_capital - initial_capital, initial_capital), 4),
        max_drawdown_pct=round(max_drawdown * 100, 4),
        trade_count=len(closed_trades),
        win_rate_pct=round(_safe_pct(len(wins), len(closed_trades)), 4),
        sharpe_ratio=round(sharpe_ratio, 4),
    )


def _execute_strategies(
    ctx: _StrategyExecutionContext, selected: list[UniverseCandidate]
) -> list[StrategyBacktestRun]:
    if not selected:
        return []

    strategy_runs: list[StrategyBacktestRun] = []
    benchmark_curve: list[BenchmarkPoint] = []
    try:
        benchmark_curve = _fetch_kospi_benchmark_curve(ctx.start_date, ctx.end_date)
    except Exception:
        benchmark_curve = []
    trade_candidates = selected[: ctx.max_positions]
    capital_per_symbol = ctx.initial_capital / max(len(trade_candidates), 1)
    trade_symbols = {c.item.symbol for c in trade_candidates}

    for candidate in selected:
        if candidate.item.symbol not in trade_symbols:
            candidate.item.allocated_budget = 0.0
            candidate.item.max_buyable_quantity = 0
            continue
        candidate.item.allocated_budget = round(capital_per_symbol, 2)
        candidate.item.max_buyable_quantity = int(
            (capital_per_symbol * _POSITION_SIZE_PCT) // candidate.item.current_price
        )

    for strategy_id in ctx.strategy_ids:
        strategy = get_strategy_definition(strategy_id)
        results: list[BacktestResponse] = []

        for candidate in trade_candidates:
            windowed = [c for c in candidate.candles if c.timestamp.date() <= ctx.end_date]
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
                        entry_trend_filter=ctx.trend_filter,
                        entry_rsi_min=ctx.rsi_min,
                        entry_rsi_max=ctx.rsi_max,
                        entry_min_volume_ratio=ctx.min_volume_ratio,
                    ),
                    trade_start_date=ctx.start_date,
                )
            except ValueError:
                continue
            results.append(result)

        strategy_runs.append(StrategyBacktestRun(
            strategy=strategy.info,
            summary=_summarize_strategy(strategy.info.id, strategy.info.label, results),
            results=results,
            benchmark_curve=benchmark_curve,
        ))

    return strategy_runs


def _fetch_rank_candles(
    *,
    selection_cutoff: date,
    candle_end_date: date,
) -> list[tuple[str, str, list[OhlcvCandle], float | None]]:
    client = _get_kis_client()
    try:
        rank_items = client.get_trade_amount_rank(count=120)
    except Exception as exc:
        raise ValueError(f"거래대금 순위 조회 실패: {exc}") from exc

    if not rank_items:
        raise ValueError("거래대금 순위 데이터가 없습니다.")

    warmup_start = selection_cutoff - timedelta(days=_WARMUP_CALENDAR_DAYS)
    result: list[tuple[str, str, list[OhlcvCandle], float | None]] = []

    for item in rank_items:
        symbol = item["code"]
        try:
            rows = client.get_daily_ohlcv(symbol, warmup_start, candle_end_date)
        except Exception:
            continue
        candles = _ohlcv_rows_to_candles(rows)
        if len(candles) < _MIN_CANDLES:
            continue
        result.append((
            symbol,
            item["name"],
            candles,
            float(item["market_cap"]) if item.get("market_cap") else None,
        ))

    return result


def run_auto_backtest(request: AutoBacktestRequest) -> AutoBacktestResponse:
    selection_cutoff = request.start_date
    price_cap = request.initial_capital / 3

    all_candles = _fetch_rank_candles(
        selection_cutoff=selection_cutoff,
        candle_end_date=request.end_date,
    )
    candidates: list[UniverseCandidate] = []
    for symbol, name, candles, market_cap in all_candles:
        period_candles = [c for c in candles if c.timestamp.date() <= request.end_date]
        candidate, _ = _build_candidate(
            symbol=symbol,
            name=name,
            candles=period_candles,
            market_cap=market_cap,
            selection_cutoff=selection_cutoff,
            price_cap=price_cap,
        )
        if candidate is not None:
            candidates.append(candidate)

    selected = _rank_candidates(candidates, request.max_symbols)

    notes = [
        "KIS OpenAPI 실데이터 기반 공통 종목선정 + 전략 테스트 백테스트입니다.",
        "종목선정은 시가총액 내림차순을 우선하고, 주가가 초기자본의 1/3 이하여야 합니다.",
        f"최근 {_OVERHEAT_LOOKBACK_DAYS}일 수익률이 {_OVERHEAT_RETURN_LIMIT_PCT:.0f}%를 넘는 과열 종목은 제외합니다.",
        f"실제 매수 시뮬레이션은 상위 {request.max_positions}종목까지만 예산을 배분합니다.",
        f"전략 테스트 대상: {', '.join(request.strategy_ids)}",
    ]
    if not selected:
        notes.append("조건을 통과한 후보가 없습니다. 초기 자본을 늘리거나 제외 조건을 완화해야 합니다.")

    ctx = _StrategyExecutionContext(
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        max_positions=request.max_positions,
        strategy_ids=request.strategy_ids,
    )
    strategy_runs = _execute_strategies(ctx, selected)
    primary_results = strategy_runs[0].results if strategy_runs else []
    return AutoBacktestResponse(
        request=request,
        selected=[c.item for c in selected],
        strategy_runs=strategy_runs,
        results=primary_results,
        notes=notes,
    )


def search_stocks(q: str) -> list[StockSearchItem]:
    q_lower = q.lower().strip()
    if not q_lower:
        return []

    # 6자리 코드 → KIS API로 조회
    if q_lower.isdigit() and len(q_lower) == 6:
        client = _get_kis_client()
        info = client.get_stock_info(q_lower)
        if info:
            return [StockSearchItem(symbol=info["code"], name=info["name"], current_price=float(info["current_price"]))]
        return []

    # 이름 검색 → KIS 종목 마스터 기반 실검색, 실패 시 정적 주요 종목 리스트 fallback
    try:
        matches = search_stock_master(q_lower, limit=10)
        if matches:
            return [
                StockSearchItem(symbol=item["symbol"], name=item["name"], current_price=0.0)
                for item in matches
            ]
    except Exception:
        pass

    fallback_results: list[StockSearchItem] = []
    for code, name in _KNOWN_STOCKS:
        if q_lower in name.lower():
            fallback_results.append(StockSearchItem(symbol=code, name=name, current_price=0.0))
        if len(fallback_results) >= 10:
            break
    return fallback_results


def get_stock_detail(symbol: str, selection_date: date | None = None) -> StockDetailResponse:
    client = _get_kis_client()
    basic_info = client.get_stock_basic_info(symbol)
    quote = client.get_stock_quote(symbol)

    if not basic_info and not quote:
        raise ValueError(f"{symbol} 종목 상세 정보를 조회하지 못했습니다.")

    name = (
        str(basic_info.get("prdt_abrv_name") or basic_info.get("prdt_name") or quote.get("hts_kor_isnm") or "").strip()
        or symbol
    )

    today_date = datetime.now().date()
    chart_end = today_date
    if selection_date is not None:
        chart_start = max(selection_date - timedelta(days=120), date(1990, 1, 1))
    else:
        chart_start = max(today_date - timedelta(days=180), date(1990, 1, 1))

    chart_rows = client.get_daily_ohlcv(symbol, chart_start, chart_end)
    chart_candles = [
        StockDetailCandle(
            candle_date=datetime.strptime(row["date"], "%Y%m%d").date(),
            open_price=float(row["open"]),
            high_price=float(row["high"]),
            low_price=float(row["low"]),
            close_price=float(row["close"]),
            volume=float(row["volume"]),
        )
        for row in chart_rows
    ]

    candle_date: date | None = None
    selection_candle: StockDetailCandle | None = None
    if selection_date is not None:
        selection_candle = next(
            (candle for candle in reversed(chart_candles) if candle.candle_date <= selection_date),
            None,
        )
        if selection_candle is not None:
            candle_date = selection_candle.candle_date

    return StockDetailResponse(
        symbol=symbol,
        name=name,
        market_name=str(basic_info.get("prdt_dvsn_name") or basic_info.get("std_idst_clsf_cd_name") or "").strip() or None,
        sector_name=str(basic_info.get("idx_bztp_scls_cd_name") or basic_info.get("prdt_name120") or "").strip() or None,
        current_price=_optional_float(quote.get("stck_prpr") or basic_info.get("thdt_clpr") or basic_info.get("bfdy_clpr")),
        previous_close=_optional_float(quote.get("stck_sdpr")),
        change_amount=_optional_float(quote.get("prdy_vrss")),
        change_rate=_optional_float(quote.get("prdy_ctrt")),
        open_price=_optional_float(quote.get("stck_oprc")),
        high_price=_optional_float(quote.get("stck_hgpr")),
        low_price=_optional_float(quote.get("stck_lwpr")),
        volume=_optional_float(quote.get("acml_vol")),
        trade_amount=_optional_float(quote.get("acml_tr_pbmn")),
        market_cap=_optional_float(quote.get("hts_avls")),
        shares_outstanding=_optional_float(quote.get("lstn_stcn")),
        week52_high=_optional_float(quote.get("w52_hgpr")),
        week52_low=_optional_float(quote.get("w52_lwpr")),
        per=_optional_float(quote.get("per")),
        pbr=_optional_float(quote.get("pbr")),
        eps=_optional_float(quote.get("eps")),
        bps=_optional_float(quote.get("bps")),
        selection_date=selection_date,
        candle_date=candle_date,
        selection_open_price=selection_candle.open_price if selection_candle else None,
        selection_high_price=selection_candle.high_price if selection_candle else None,
        selection_low_price=selection_candle.low_price if selection_candle else None,
        selection_close_price=selection_candle.close_price if selection_candle else None,
        selection_volume=selection_candle.volume if selection_candle else None,
        chart_candles=chart_candles,
    )


def run_stock_selection(request: StockSelectionRequest) -> StockSelectionResponse:
    selection_cutoff = request.selection_date + timedelta(days=1)
    price_cap = request.initial_capital / 3

    all_candles = _fetch_rank_candles(
        selection_cutoff=selection_cutoff,
        candle_end_date=request.selection_date,
    )
    candidates: list[UniverseCandidate] = []
    for symbol, name, candles, market_cap in all_candles:
        candidate, _ = _build_candidate(
            symbol=symbol,
            name=name,
            candles=candles,
            market_cap=market_cap,
            selection_cutoff=selection_cutoff,
            price_cap=price_cap,
        )
        if candidate is not None:
            candidates.append(candidate)

    selected = _rank_candidates(candidates, request.max_symbols)

    notes = [
        "KIS OpenAPI 실데이터 기반 종목선정입니다.",
        f"기준일: {request.selection_date}",
        "종목선정은 시가총액 내림차순, 주가 상한, 최근 과열 제외 기준을 사용합니다.",
        f"과열 제외: 최근 {_OVERHEAT_LOOKBACK_DAYS}일 수익률 {_OVERHEAT_RETURN_LIMIT_PCT:.0f}% 초과 종목",
    ]
    if not selected:
        notes.append("조건을 통과한 후보가 없습니다. 초기 자본을 늘리거나 제외 조건을 완화해야 합니다.")

    return StockSelectionResponse(selected=[c.item for c in selected], notes=notes)


def run_stock_selection_range(request: StockSelectionRangeRequest) -> StockSelectionRangeResponse:
    price_cap = request.initial_capital / 3
    days = _market_days(request.start_date, request.end_date)

    all_candles = _fetch_rank_candles(
        selection_cutoff=request.start_date,
        candle_end_date=request.end_date,
    )

    date_results: list[StockSelectionDateResult] = []

    for day in days:
        selection_cutoff = day + timedelta(days=1)
        day_candidates: list[UniverseCandidate] = []

        for symbol, name, candles, market_cap in all_candles:
            candidate, _ = _build_candidate(
                symbol=symbol,
                name=name,
                candles=candles,
                market_cap=market_cap,
                selection_cutoff=selection_cutoff,
                price_cap=price_cap,
            )
            if candidate is not None:
                day_candidates.append(candidate)

        ranked = _rank_candidates(day_candidates, request.max_symbols)
        date_results.append(StockSelectionDateResult(
            selection_date=day,
            selected=[c.item for c in ranked],
        ))

    notes = [
        "KIS OpenAPI 실데이터 기반 기간별 종목선정입니다.",
        f"분석 기간: {request.start_date} ~ {request.end_date} ({len(days)}개 영업일)",
        "종목선정은 시가총액 내림차순, 주가 상한, 최근 과열 제외 기준을 사용합니다.",
    ]

    return StockSelectionRangeResponse(results=date_results, notes=notes)


def run_strategies_only(request: StrategyOnlyRequest) -> StrategyRunsResponse:
    selection_cutoff = request.start_date
    client = _get_kis_client()

    candidates: list[UniverseCandidate] = []
    skipped: list[str] = []

    warmup_start = selection_cutoff - timedelta(days=_WARMUP_CALENDAR_DAYS)
    for sym in request.symbols:
        try:
            rows = client.get_daily_ohlcv(sym.symbol, warmup_start, request.end_date)
        except Exception:
            skipped.append(sym.symbol)
            continue

        candles = _ohlcv_rows_to_candles(rows)
        if len(candles) < 80:
            skipped.append(sym.symbol)
            continue

        sel_candles = [c for c in candles if c.timestamp.date() < selection_cutoff]
        if not sel_candles:
            skipped.append(sym.symbol)
            continue

        recent = sel_candles[-20:]
        avg_trade_amount = sum(c.close * c.volume for c in recent) / max(len(recent), 1)

        candidates.append(UniverseCandidate(
            item=StockSelectionItem(
                symbol=sym.symbol,
                name=sym.name,
                avg_trade_amount=round(avg_trade_amount, 2),
                current_price=float(sel_candles[-1].close),
                market_cap=None,
                allocated_budget=0.0,
                max_buyable_quantity=None,
                score=0.0,
                reason="직접 선택",
            ),
            candles=candles,
            recent_return_pct=0.0,
        ))

    notes: list[str] = []
    if skipped:
        notes.append(f"데이터 조회 실패 종목: {', '.join(skipped)}")

    if not candidates:
        return StrategyRunsResponse(
            strategy_runs=[],
            notes=notes + ["백테스트에 필요한 일봉 데이터가 부족한 종목만 선택되어 실행할 수 없습니다."],
        )

    ctx = _StrategyExecutionContext(
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        max_positions=len(candidates),
        strategy_ids=request.strategy_ids,
        trend_filter=request.trend_filter,
        rsi_min=request.rsi_min,
        rsi_max=request.rsi_max,
        min_volume_ratio=request.min_volume_ratio,
    )
    strategy_runs = _execute_strategies(ctx, candidates)
    notes.append(f"전략 테스트 대상: {', '.join(request.strategy_ids)}")
    notes.append(
        "적용 필터(진입 시점 기준): "
        f"추세={request.trend_filter}, "
        f"RSI={request.rsi_min if request.rsi_min is not None else '-'}~{request.rsi_max if request.rsi_max is not None else '-'}, "
        f"거래량비율>={request.min_volume_ratio if request.min_volume_ratio is not None else '-'}"
    )

    return StrategyRunsResponse(strategy_runs=strategy_runs, notes=notes)
