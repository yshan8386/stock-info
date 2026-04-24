from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from app.schemas.backtest import (
    BacktestConfig,
    BacktestResponse,
    OhlcvCandle,
    StrategyInfo,
)
from app.services.backtest_engine import (
    run_pullback_rebound_backtest,
    run_support_resistance_backtest,
)


StrategyRunner = Callable[..., BacktestResponse]


@dataclass(frozen=True)
class StrategyDefinition:
    info: StrategyInfo
    runner: StrategyRunner


_STRATEGIES: dict[str, StrategyDefinition] = {
    "pullback_rebound_v1": StrategyDefinition(
        info=StrategyInfo(
            id="pullback_rebound_v1",
            label="눌림목 반등",
            description="상승 추세에서 이동평균선/지지선 부근 눌림 이후 반등하는 종목을 추적합니다.",
        ),
        runner=run_pullback_rebound_backtest,
    ),
    "support_resistance_v1": StrategyDefinition(
        info=StrategyInfo(
            id="support_resistance_v1",
            label="지지·저항 돌파",
            description="지지선 반등과 저항선 돌파 신호를 이용해 추세 지속 구간을 추적합니다.",
        ),
        runner=run_support_resistance_backtest,
    ),
}


def list_strategy_definitions() -> list[StrategyDefinition]:
    return list(_STRATEGIES.values())


def list_strategies() -> list[StrategyInfo]:
    return [definition.info for definition in list_strategy_definitions()]


def get_strategy_definition(strategy_id: str) -> StrategyDefinition:
    try:
        return _STRATEGIES[strategy_id]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 전략입니다: {strategy_id}") from exc
