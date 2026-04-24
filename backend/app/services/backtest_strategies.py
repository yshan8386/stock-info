from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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


_STRATEGY_METADATA_PATH = (
    Path(__file__).parents[2] / "data" / "backtest_strategies.json"
)

_RUNNERS: dict[str, StrategyRunner] = {
    "pullback_rebound_v1": run_pullback_rebound_backtest,
    "support_resistance_v1": run_support_resistance_backtest,
}


def _load_strategy_infos() -> list[StrategyInfo]:
    raw_items = json.loads(_STRATEGY_METADATA_PATH.read_text(encoding="utf-8"))
    return [StrategyInfo.model_validate(item) for item in raw_items]


def _build_strategy_map() -> dict[str, StrategyDefinition]:
    strategy_map: dict[str, StrategyDefinition] = {}
    for info in _load_strategy_infos():
        runner = _RUNNERS.get(info.id)
        if runner is None:
            raise ValueError(f"전략 러너가 등록되지 않았습니다: {info.id}")
        strategy_map[info.id] = StrategyDefinition(info=info, runner=runner)
    return strategy_map


def list_strategy_definitions() -> list[StrategyDefinition]:
    return list(_build_strategy_map().values())


def list_strategies() -> list[StrategyInfo]:
    return [definition.info for definition in list_strategy_definitions()]


def get_strategy_definition(strategy_id: str) -> StrategyDefinition:
    strategy_map = _build_strategy_map()
    try:
        return strategy_map[strategy_id]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 전략입니다: {strategy_id}") from exc
