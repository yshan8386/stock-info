from app.api.position import DEFAULT_STRATEGY_IDS
from app.services.backtest_strategies import list_strategies


def test_position_strategies_include_new_live_dashboard_choices() -> None:
    strategy_ids = {strategy.id for strategy in list_strategies()}

    assert DEFAULT_STRATEGY_IDS[0] in strategy_ids
    assert "breakout_volume_v1" in strategy_ids
    assert "trend_follow_v1" in strategy_ids
    assert "rsi_reversal_v1" in strategy_ids


def test_live_dashboard_does_not_ship_synthetic_signal_universe() -> None:
    from app.api import position

    assert not hasattr(position, "SIGNAL_UNIVERSE")
