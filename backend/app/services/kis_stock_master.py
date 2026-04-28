from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import httpx

_CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "stock_master_cache.json"
_CACHE_TTL = timedelta(hours=24)


@dataclass(frozen=True)
class MasterSource:
    market: str
    url: str
    trailer_width: int


_SOURCES: tuple[MasterSource, ...] = (
    MasterSource(
        market="KOSPI",
        url="https://new.real.download.dws.co.kr/common/master/kospi_code.mst.zip",
        trailer_width=228,
    ),
    MasterSource(
        market="KOSDAQ",
        url="https://new.real.download.dws.co.kr/common/master/kosdaq_code.mst.zip",
        trailer_width=222,
    ),
)

_memory_cache: list[dict[str, str]] | None = None
_memory_loaded_at: datetime | None = None


def search_stock_master(query: str, limit: int = 10) -> list[dict[str, str]]:
    q = query.strip().casefold()
    if not q:
        return []

    items = load_stock_master()
    results: list[dict[str, str]] = []
    for item in items:
        symbol = item["symbol"]
        name = item["name"]
        if q in name.casefold() or q in symbol:
            results.append(item)
        if len(results) >= limit:
            break
    return results


def load_stock_master(force_refresh: bool = False) -> list[dict[str, str]]:
    global _memory_cache, _memory_loaded_at

    now = datetime.now()
    if (
        not force_refresh
        and _memory_cache is not None
        and _memory_loaded_at is not None
        and now - _memory_loaded_at < _CACHE_TTL
    ):
        return _memory_cache

    if not force_refresh:
        cached = _read_cache()
        if cached is not None:
            _memory_cache = cached
            _memory_loaded_at = now
            return cached

    try:
        fresh = _download_stock_master()
        _write_cache(fresh)
        _memory_cache = fresh
        _memory_loaded_at = now
        return fresh
    except Exception:
        cached = _read_cache(allow_stale=True)
        if cached is not None:
            _memory_cache = cached
            _memory_loaded_at = now
            return cached
        raise


def _read_cache(allow_stale: bool = False) -> list[dict[str, str]] | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        created_at = datetime.fromisoformat(payload["created_at"])
        if not allow_stale and datetime.now() - created_at >= _CACHE_TTL:
            return None
        items = payload.get("items", [])
        if not isinstance(items, list):
            return None
        return [
            {
                "symbol": str(item["symbol"]),
                "name": str(item["name"]),
                "market": str(item.get("market", "")),
            }
            for item in items
            if isinstance(item, dict) and item.get("symbol") and item.get("name")
        ]
    except Exception:
        return None


def _write_cache(items: list[dict[str, str]]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps(
            {
                "created_at": datetime.now().isoformat(),
                "items": items,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _download_stock_master() -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []
    seen: set[str] = set()

    with httpx.Client(timeout=20, follow_redirects=True, verify=False) as client:
        for source in _SOURCES:
            response = client.get(source.url)
            response.raise_for_status()
            collected.extend(_parse_master_zip(response.content, source.market, source.trailer_width, seen))
    return collected


def _parse_master_zip(
    content: bytes,
    market: str,
    trailer_width: int,
    seen: set[str],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        member_name = next((name for name in archive.namelist() if name.endswith(".mst")), None)
        if member_name is None:
            raise ValueError(f"{market} 종목 마스터 압축 파일에 .mst 데이터가 없습니다.")
        raw = archive.read(member_name).decode("cp949")

    for line in raw.splitlines():
        row = line.rstrip("\r\n")
        if len(row) <= trailer_width:
            continue
        payload = row[:-trailer_width]
        symbol = payload[0:9].strip()
        name = payload[21:].strip()
        if not symbol or not name or symbol in seen:
            continue
        seen.add(symbol)
        rows.append({
            "symbol": symbol,
            "name": name,
            "market": market,
        })
    return rows
