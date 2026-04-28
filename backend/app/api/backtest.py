from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.backtest import (
    AutoBacktestRequest,
    AutoBacktestResponse,
    BacktestResponse,
    KisOhlcvEndpointInfo,
    ManualBacktestRequest,
    SelectedSymbol,
    StockDetailResponse,
    StockSearchItem,
    StockSelectionRangeRequest,
    StockSelectionRangeResponse,
    StockSelectionRequest,
    StockSelectionResponse,
    StrategyInfo,
    StrategyOnlyRequest,
    StrategyRunsResponse,
)
from app.services.backtest_engine import run_support_resistance_backtest
from app.services.backtest_strategies import list_strategies
from app.services.backtest_selector import (
    get_stock_detail,
    run_auto_backtest,
    run_stock_selection,
    run_stock_selection_range,
    run_strategies_only,
    search_stocks,
)
from app.services.kis_market_data import KIS_OHLCV_ENDPOINTS

router = APIRouter(
    prefix="/backtest", tags=["backtest"], dependencies=[Depends(get_current_user)]
)


@router.get("/kis/ohlcv-endpoints", response_model=list[KisOhlcvEndpointInfo])
def get_kis_ohlcv_endpoints() -> list[KisOhlcvEndpointInfo]:
    return KIS_OHLCV_ENDPOINTS


@router.get("/strategies", response_model=list[StrategyInfo])
def get_backtest_strategies() -> list[StrategyInfo]:
    return list_strategies()


@router.post("/run", response_model=AutoBacktestResponse)
def run_backtest(request: AutoBacktestRequest) -> AutoBacktestResponse:
    try:
        return run_auto_backtest(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/search-stocks", response_model=list[StockSearchItem])
def search_backtest_stocks(q: str = "") -> list[StockSearchItem]:
    return search_stocks(q)


@router.get("/stocks/{symbol}/detail", response_model=StockDetailResponse)
def get_backtest_stock_detail(symbol: str, selection_date: date | None = None) -> StockDetailResponse:
    try:
        return get_stock_detail(symbol, selection_date=selection_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/select", response_model=StockSelectionResponse)
def select_stocks_only(request: StockSelectionRequest) -> StockSelectionResponse:
    try:
        return run_stock_selection(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/select-range", response_model=StockSelectionRangeResponse)
def select_stocks_range(request: StockSelectionRangeRequest) -> StockSelectionRangeResponse:
    try:
        return run_stock_selection_range(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run-strategies", response_model=StrategyRunsResponse)
def run_strategies_only_endpoint(request: StrategyOnlyRequest) -> StrategyRunsResponse:
    try:
        return run_strategies_only(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/run-manual", response_model=BacktestResponse)
def run_manual_backtest(request: ManualBacktestRequest) -> BacktestResponse:
    try:
        return run_support_resistance_backtest(
            symbol=request.symbol,
            candles=request.candles,
            config=request.config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
