from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

_TOKEN_CACHE_PATH = Path(__file__).parent.parent.parent / ".kis_token_cache.json"
_CALL_INTERVAL = 0.15  # KIS API 초당 10건 제한

_singleton: "KisMarketClient | None" = None


class KisMarketClient:
    """
    KIS OpenAPI 시세 전용 클라이언트.

    백테스트 종목선정에 필요한 두 가지만 구현한다:
    - 거래대금 상위 종목 조회
    - 종목별 일봉 OHLCV 조회 (날짜 범위, 페이지네이션 지원)
    """

    def __init__(self, app_key: str, app_secret: str, base_url: str) -> None:
        self._app_key = app_key
        self._app_secret = app_secret
        self._base_url = base_url.rstrip("/")
        self._token: str = ""
        self._token_expires_at: datetime | None = None
        self._last_call: float = 0.0
        self._load_token_cache()

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def get_trade_amount_rank(self, count: int = 30) -> list[dict[str, Any]]:
        """
        거래대금 상위 종목을 조회한다.

        반환 항목: code, name, current_price, trade_amount, market_cap
        """
        data = self._get(
            "/uapi/domestic-stock/v1/quotations/volume-rank",
            "FHPST01710000",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": "20171",
                "FID_INPUT_ISCD": "0000",
                "FID_DIV_CLS_CODE": "0",
                "FID_BLNG_CLS_CODE": "0",
                "FID_TRGT_CLS_CODE": "111111111",
                "FID_TRGT_EXLS_CLS_CODE": "000000",
                "FID_INPUT_PRICE_1": "0",
                "FID_INPUT_PRICE_2": "0",
                "FID_VOL_CNT": "0",
                "FID_INPUT_DATE_1": "",
            },
        )

        rows = data.get("output", [])
        if not isinstance(rows, list):
            rows = []

        results = []
        for item in rows:
            code = item.get("mksc_shrn_iscd", "")
            if not code:
                continue
            price = _to_int(item.get("stck_prpr"))
            listing_shares = _to_int(item.get("lstn_stcn"))
            results.append(
                {
                    "code": code,
                    "name": item.get("hts_kor_isnm", ""),
                    "current_price": price,
                    "trade_amount": _to_int(item.get("acml_tr_pbmn")),
                    "market_cap": price * listing_shares if price > 0 and listing_shares > 0 else 0,
                }
            )

        results.sort(key=lambda r: r["trade_amount"], reverse=True)
        return results[:count]

    def get_stock_info(self, symbol: str) -> dict[str, Any] | None:
        """
        종목코드로 종목명·현재가를 조회한다.

        반환: {"code": str, "name": str, "current_price": int} 또는 None
        """
        try:
            data = self._get(
                "/uapi/domestic-stock/v1/quotations/search-stock-info",
                "CTPF1002R",
                {"PRDT_TYPE_CD": "300", "PDNO": symbol},
            )
            output = data.get("output", {})
            name = output.get("prdt_abrv_name", "").strip()
            price = _to_int(output.get("thdt_clpr") or output.get("bfdy_clpr"))
            if not name:
                return None
            return {"code": symbol, "name": name, "current_price": price}
        except Exception:
            return None

    def get_stock_basic_info(self, symbol: str) -> dict[str, Any]:
        """주식기본조회 API로 종목 메타데이터를 조회한다."""
        data = self._get(
            "/uapi/domestic-stock/v1/quotations/search-stock-info",
            "CTPF1002R",
            {"PRDT_TYPE_CD": "300", "PDNO": symbol},
        )
        output = data.get("output", {})
        return output if isinstance(output, dict) else {}

    def get_stock_quote(self, symbol: str) -> dict[str, Any]:
        """주식현재가 시세 API로 현재 시세와 기본 지표를 조회한다."""
        data = self._get(
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
            },
        )
        output = data.get("output", {})
        return output if isinstance(output, dict) else {}

    def get_daily_ohlcv(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        종목의 일봉 데이터를 조회한다 (날짜 범위, 100일 초과 시 자동 페이지네이션).

        반환: [{"date": "YYYYMMDD", "open": int, "high": int, "low": int,
                 "close": int, "volume": int}, ...]  날짜 오름차순
        """
        collected: dict[str, dict[str, Any]] = {}
        current_end = end_date

        while current_end >= start_date:
            data = self._get(
                "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
                "FHKST03010100",
                {
                    "FID_COND_MRKT_DIV_CODE": "J",
                    "FID_INPUT_ISCD": symbol,
                    "FID_INPUT_DATE_1": start_date.strftime("%Y%m%d"),
                    "FID_INPUT_DATE_2": current_end.strftime("%Y%m%d"),
                    "FID_PERIOD_DIV_CODE": "D",
                    "FID_ORG_ADJ_PRC": "0",
                },
            )
            rows = data.get("output2", [])
            if not rows:
                break

            for row in rows:
                date_str = row.get("stck_bsop_date", "")
                if not date_str:
                    continue
                collected[date_str] = {
                    "date": date_str,
                    "open": _to_int(row.get("stck_oprc")),
                    "high": _to_int(row.get("stck_hgpr")),
                    "low": _to_int(row.get("stck_lwpr")),
                    "close": _to_int(row.get("stck_clpr")),
                    "volume": _to_int(row.get("acml_vol")),
                }

            earliest_str = min(collected.keys())
            earliest = datetime.strptime(earliest_str, "%Y%m%d").date()

            if earliest <= start_date or len(rows) < 100:
                break

            current_end = earliest - timedelta(days=1)

        return sorted(collected.values(), key=lambda r: r["date"])

    # ------------------------------------------------------------------
    # 내부 구현
    # ------------------------------------------------------------------

    def _ensure_token(self) -> bool:
        if self._token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return True
        try:
            resp = httpx.post(
                f"{self._base_url}/oauth2/tokenP",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self._app_key,
                    "appsecret": self._app_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            payload = resp.json()
            self._token = payload["access_token"]
            self._token_expires_at = datetime.now() + timedelta(hours=23)
            self._save_token_cache()
            return True
        except Exception:
            return False

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_call
        if elapsed < _CALL_INTERVAL:
            time.sleep(_CALL_INTERVAL - elapsed)
        self._last_call = time.time()

    def _get(self, path: str, tr_id: str, params: dict[str, str]) -> dict[str, Any]:
        if not self._ensure_token():
            return {}
        self._throttle()
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._token}",
            "appkey": self._app_key,
            "appsecret": self._app_secret,
            "tr_id": tr_id,
        }
        try:
            resp = httpx.get(
                f"{self._base_url}{path}",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("rt_cd") != "0":
                return {}
            return data
        except Exception:
            return {}

    def _save_token_cache(self) -> None:
        try:
            _TOKEN_CACHE_PATH.write_text(
                json.dumps(
                    {
                        "token": self._token,
                        "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else "",
                    }
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_token_cache(self) -> None:
        if not _TOKEN_CACHE_PATH.exists():
            return
        try:
            cache = json.loads(_TOKEN_CACHE_PATH.read_text(encoding="utf-8"))
            expires_at = datetime.fromisoformat(cache.get("expires_at", ""))
            if datetime.now() < expires_at:
                self._token = cache["token"]
                self._token_expires_at = expires_at
        except Exception:
            pass


def get_client(app_key: str, app_secret: str, base_url: str) -> "KisMarketClient":
    """프로세스 내에서 KisMarketClient 인스턴스를 재사용한다 (토큰 재발급 최소화)."""
    global _singleton
    if _singleton is None:
        _singleton = KisMarketClient(app_key=app_key, app_secret=app_secret, base_url=base_url)
    return _singleton


def _to_int(value: Any) -> int:
    try:
        return int(str(value).replace(",", "").strip() or 0)
    except (TypeError, ValueError):
        return 0
