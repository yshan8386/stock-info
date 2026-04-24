from app.schemas.backtest import KisOhlcvEndpointInfo


KIS_OHLCV_ENDPOINTS = [
    KisOhlcvEndpointInfo(
        market="domestic_stock",
        timeframe="daily",
        endpoint="/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
        tr_id="FHKST03010100",
        max_rows_per_call=100,
        output="output2",
        fields={
            "timestamp": "stck_bsop_date",
            "open": "stck_oprc",
            "high": "stck_hgpr",
            "low": "stck_lwpr",
            "close": "stck_clpr",
            "volume": "acml_vol",
        },
    ),
    KisOhlcvEndpointInfo(
        market="domestic_stock",
        timeframe="minute",
        endpoint="/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice",
        tr_id="FHKST03010230",
        max_rows_per_call=120,
        output="output2",
        fields={
            "timestamp": "stck_bsop_date + stck_cntg_hour",
            "open": "stck_oprc",
            "high": "stck_hgpr",
            "low": "stck_lwpr",
            "close": "stck_prpr",
            "volume": "cntg_vol",
        },
    ),
]
