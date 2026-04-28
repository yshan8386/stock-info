from app.api.position import DEFAULT_STRATEGY_IDS, SIGNAL_UNIVERSE
from app.services.backtest_strategies import list_strategies


def test_position_strategies_include_new_live_dashboard_choices() -> None:
    strategy_ids = {strategy.id for strategy in list_strategies()}

    assert DEFAULT_STRATEGY_IDS[0] in strategy_ids
    assert "breakout_volume_v1" in strategy_ids
    assert "trend_follow_v1" in strategy_ids
    assert "rsi_reversal_v1" in strategy_ids


def test_signal_universe_uses_registered_strategy_ids() -> None:
    strategy_ids = {strategy.id for strategy in list_strategies()}

    assert SIGNAL_UNIVERSE
    assert {signal["strategy_id"] for signal in SIGNAL_UNIVERSE}.issubset(strategy_ids)
