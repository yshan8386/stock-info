from datetime import date

from app.services import backtest_selector


class _FakeKisClient:
    def get_stock_basic_info(self, symbol: str) -> dict[str, str]:
        assert symbol == "005930"
        return {
            "prdt_abrv_name": "삼성전자",
            "prdt_dvsn_name": "KOSPI",
            "idx_bztp_scls_cd_name": "전기전자",
        }

    def get_stock_quote(self, symbol: str) -> dict[str, str]:
        assert symbol == "005930"
        return {
            "stck_prpr": "71000",
            "stck_sdpr": "70000",
            "prdy_vrss": "1000",
            "prdy_ctrt": "1.43",
            "stck_oprc": "70500",
            "stck_hgpr": "71500",
            "stck_lwpr": "70200",
            "acml_vol": "12345678",
            "acml_tr_pbmn": "876543210000",
            "hts_avls": "423000000000000",
            "lstn_stcn": "5969782550",
            "w52_hgpr": "88800",
            "w52_lwpr": "63500",
            "per": "18.50",
            "pbr": "1.42",
            "eps": "3830",
            "bps": "50000",
        }

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, int | str]]:
        assert symbol == "005930"
        assert start_date <= date(2025, 2, 14)
        assert end_date >= date(2025, 2, 14)
        return [
            {
                "date": "20250213",
                "open": 69500,
                "high": 70500,
                "low": 69400,
                "close": 70100,
                "volume": 10000000,
            },
            {
                "date": "20250214",
                "open": 70200,
                "high": 71000,
                "low": 70000,
                "close": 70900,
                "volume": 11223344,
            },
        ]


def test_get_stock_detail_combines_current_quote_and_selection_candle(monkeypatch) -> None:
    monkeypatch.setattr(backtest_selector, "_get_kis_client", lambda: _FakeKisClient())

    detail = backtest_selector.get_stock_detail("005930", selection_date=date(2025, 2, 14))

    assert detail.symbol == "005930"
    assert detail.name == "삼성전자"
    assert detail.market_name == "KOSPI"
    assert detail.sector_name == "전기전자"
    assert detail.current_price == 71000
    assert detail.change_rate == 1.43
    assert detail.selection_date == date(2025, 2, 14)
    assert detail.candle_date == date(2025, 2, 14)
    assert detail.selection_close_price == 70900
    assert detail.selection_volume == 11223344
    assert len(detail.chart_candles) == 2
    assert detail.chart_candles[-1].candle_date == date(2025, 2, 14)
    assert detail.chart_candles[-1].close_price == 70900
