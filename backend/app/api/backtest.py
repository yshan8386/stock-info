from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.schemas.backtest import (
    AutoBacktestRequest,
    AutoBacktestResponse,
    BacktestResponse,
    KisOhlcvEndpointInfo,
    ManualBacktestRequest,
    StrategyInfo,
)
from app.services.backtest_engine import run_support_resistance_backtest
from app.services.backtest_strategies import list_strategies
from app.services.backtest_selector import run_auto_backtest
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
