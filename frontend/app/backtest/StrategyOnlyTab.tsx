"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type { SelectedSymbol, StockSearchItem, StrategyInfo, StrategyRunsResult } from "@/types/api";
import { Metric, NotesList, StrategyResults } from "./_shared";

const DEFAULT_STRATEGIES: StrategyInfo[] = [
  {
    id: "pullback_rebound_v1",
    label: "눌림목 반등",
    description: "상승 추세에서 눌림 이후 반등하는 종목을 추적합니다.",
  },
  {
    id: "support_resistance_v1",
    label: "지지·저항 돌파",
    description: "지지선 반등과 저항선 돌파 신호를 이용해 추세 지속 구간을 추적합니다.",
  },
];

type TrendFilter = "none" | "price_above_ma60" | "ma20_above_ma60" | "ma5_ma20_ma60_bullish";

const STRATEGY_FILTER_PRESETS: Record<string, { trendFilter: TrendFilter; rsiMin: string; rsiMax: string; minVolumeRatio: string }> = {
  pullback_rebound_v1: {
    trendFilter: "ma20_above_ma60",
    rsiMin: "40",
    rsiMax: "60",
    minVolumeRatio: "1.10",
  },
  support_resistance_v1: {
    trendFilter: "price_above_ma60",
    rsiMin: "50",
    rsiMax: "75",
    minVolumeRatio: "1.50",
  },
};

const TREND_FILTER_OPTIONS: { value: TrendFilter; label: string }[] = [
  { value: "none", label: "없음" },
  { value: "price_above_ma60", label: "종가가 60일선 위" },
  { value: "ma20_above_ma60", label: "20일선 > 60일선" },
  { value: "ma5_ma20_ma60_bullish", label: "5일선 > 20일선 > 60일선" },
];

function FilterToggle({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="inline-flex items-center gap-2 text-sm font-medium text-text">
      <input
        checked={checked}
        className="h-4 w-4 accent-[#0f8a65]"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
      {label}
    </label>
  );
}

function today(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString().slice(0, 10);
}

function parsePositiveNumber(value: string, label: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) throw new Error(`${label}은 0보다 큰 숫자로 입력하세요.`);
  return parsed;
}

function parseNonNegativeNumber(value: string, label: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`${label}은 0 이상의 숫자로 입력하세요.`);
  return parsed;
}

export function StrategyOnlyTab({
  strategies,
  preloadedStocks,
}: {
  strategies: StrategyInfo[];
  preloadedStocks: SelectedSymbol[] | null;
}) {
  const allStrategies = strategies.length ? strategies : DEFAULT_STRATEGIES;

  const [selectedSymbols, setSelectedSymbols] = useState<SelectedSymbol[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<StockSearchItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const [startDate, setStartDate] = useState(today(-180));
  const [endDate, setEndDate] = useState(today());
  const [capital, setCapital] = useState("2000000");
  const [strategyId, setStrategyId] = useState<string>(allStrategies[0]?.id ?? DEFAULT_STRATEGIES[0].id);
  const [useTrendFilter, setUseTrendFilter] = useState(true);
  const [trendFilter, setTrendFilter] = useState<TrendFilter>("ma20_above_ma60");
  const [useRsiFilter, setUseRsiFilter] = useState(true);
  const [rsiMin, setRsiMin] = useState("40");
  const [rsiMax, setRsiMax] = useState("60");
  const [useVolumeFilter, setUseVolumeFilter] = useState(true);
  const [minVolumeRatio, setMinVolumeRatio] = useState("1.10");

  const [searchError, setSearchError] = useState<string | null>(null);

  const [result, setResult] = useState<StrategyRunsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!allStrategies.some((strategy) => strategy.id === strategyId)) {
      setStrategyId(allStrategies[0]?.id ?? DEFAULT_STRATEGIES[0].id);
    }
  }, [allStrategies, strategyId]);

  useEffect(() => {
    const preset =
      STRATEGY_FILTER_PRESETS[strategyId] ??
      { trendFilter: "none" as TrendFilter, rsiMin: "", rsiMax: "", minVolumeRatio: "" };
    setUseTrendFilter(preset.trendFilter !== "none");
    setTrendFilter(preset.trendFilter);
    setUseRsiFilter(Boolean(preset.rsiMin || preset.rsiMax));
    setRsiMin(preset.rsiMin);
    setRsiMax(preset.rsiMax);
    setUseVolumeFilter(Boolean(preset.minVolumeRatio));
    setMinVolumeRatio(preset.minVolumeRatio);
  }, [strategyId]);

  // Debounced stock search
  useEffect(() => {
    const q = searchQuery.trim();
    if (!q) {
      setSearchResults([]);
      setDropdownOpen(false);
      return;
    }
    const timer = setTimeout(async () => {
      setSearchLoading(true);
      setSearchError(null);
      try {
        const results = await apiFetch<StockSearchItem[]>(
          `/backtest/search-stocks?q=${encodeURIComponent(q)}`
        );
        setSearchResults(results);
        setDropdownOpen(results.length > 0);
        if (results.length === 0) setSearchError("검색 결과가 없습니다.");
      } catch (exc) {
        setSearchResults([]);
        setSearchError(exc instanceof Error ? exc.message : "종목 검색에 실패했습니다. 백엔드 서버를 확인하세요.");
      } finally {
        setSearchLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function addSymbol(stock: StockSearchItem) {
    if (selectedSymbols.length >= 5) return;
    if (selectedSymbols.some((s) => s.symbol === stock.symbol)) return;
    setSelectedSymbols((prev) => [...prev, { symbol: stock.symbol, name: stock.name }]);
    setSearchQuery("");
    setDropdownOpen(false);
  }

  function removeSymbol(symbol: string) {
    setSelectedSymbols((prev) => prev.filter((s) => s.symbol !== symbol));
  }

  function loadPreloaded() {
    if (!preloadedStocks) return;
    const toAdd = preloadedStocks.filter((p) => !selectedSymbols.some((s) => s.symbol === p.symbol));
    const combined = [...selectedSymbols, ...toAdd].slice(0, 5);
    setSelectedSymbols(combined);
  }

  async function run() {
    setError(null);
    let parsedCapital: number;
    let parsedRsiMin: number | null = null;
    let parsedRsiMax: number | null = null;
    let parsedMinVolumeRatio: number | null = null;
    try {
      if (selectedSymbols.length === 0) throw new Error("최소 1개 종목을 추가하세요.");
      if (!startDate || !endDate) throw new Error("시작일과 종료일을 모두 입력하세요.");
      if (startDate >= endDate) throw new Error("종료일은 시작일보다 뒤여야 합니다.");
      parsedCapital = parsePositiveNumber(capital, "초기 자본");
      if (!strategyId) throw new Error("전략을 선택하세요.");
      if (useRsiFilter && rsiMin.trim()) parsedRsiMin = parseNonNegativeNumber(rsiMin, "RSI 최소값");
      if (useRsiFilter && rsiMax.trim()) parsedRsiMax = parseNonNegativeNumber(rsiMax, "RSI 최대값");
      if (parsedRsiMin != null && parsedRsiMin > 100) throw new Error("RSI 최소값은 100 이하로 입력하세요.");
      if (parsedRsiMax != null && parsedRsiMax > 100) throw new Error("RSI 최대값은 100 이하로 입력하세요.");
      if (parsedRsiMin != null && parsedRsiMax != null && parsedRsiMin > parsedRsiMax) {
        throw new Error("RSI 최소값은 최대값보다 작거나 같아야 합니다.");
      }
      if (useVolumeFilter && minVolumeRatio.trim()) {
        parsedMinVolumeRatio = parsePositiveNumber(minVolumeRatio, "최소 거래량 비율");
      }
    } catch (exc) {
      setResult(null);
      setError(exc instanceof Error ? exc.message : "입력값을 확인하세요.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch<StrategyRunsResult>("/backtest/run-strategies", {
        method: "POST",
        body: JSON.stringify({
          symbols: selectedSymbols,
          start_date: startDate,
          end_date: endDate,
          initial_capital: parsedCapital,
          strategy_ids: [strategyId],
          trend_filter: useTrendFilter ? trendFilter : "none",
          rsi_min: useRsiFilter ? parsedRsiMin : null,
          rsi_max: useRsiFilter ? parsedRsiMax : null,
          min_volume_ratio: useVolumeFilter ? parsedMinVolumeRatio : null,
        }),
      });
      setResult(data);
    } catch (exc) {
      setResult(null);
      setError(exc instanceof Error ? exc.message : "전략 테스트 실행에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  const selectedStrategy = allStrategies.find((strategy) => strategy.id === strategyId) ?? allStrategies[0];

  return (
    <div className="space-y-6">
      <section className="surface rounded-md p-5">
        {/* Stock selection */}
        <div>
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-text">
              종목 선택 <span className="font-normal text-muted">({selectedSymbols.length}/5)</span>
            </p>
            {preloadedStocks && preloadedStocks.length > 0 && (
              <button
                className="rounded-md border border-info bg-infoSoft px-3 py-1 text-xs font-semibold text-info transition hover:bg-info hover:text-white"
                onClick={loadPreloaded}
                type="button"
              >
                이전 선정 결과 불러오기 ({Math.min(preloadedStocks.length, 5)}개)
              </button>
            )}
          </div>

          {/* Search input */}
          <div ref={searchRef} className="relative mt-2">
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-md border border-line bg-white px-3 py-2 text-sm outline-none focus:border-accent"
                disabled={selectedSymbols.length >= 5}
                onChange={(e) => { setSearchQuery(e.target.value); setSearchError(null); }}
                placeholder={selectedSymbols.length >= 5 ? "최대 5개까지 선택 가능합니다" : "종목코드 또는 종목명 검색 (예: 삼성전자, 005930)"}
                type="text"
                value={searchQuery}
              />
              {searchLoading && (
                <span className="flex items-center px-2 text-sm text-muted">검색 중...</span>
              )}
            </div>
            {searchError && !dropdownOpen && searchQuery.trim() && (
              <p className="mt-1 text-xs text-coral">{searchError}</p>
            )}
            {dropdownOpen && searchResults.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full rounded-md border border-line bg-white shadow-lg">
                {searchResults.map((item) => (
                  <li key={item.symbol}>
                    <button
                      className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-accentSoft"
                      onClick={() => addSymbol(item)}
                      type="button"
                    >
                      <span>
                        <span className="font-semibold">{item.name}</span>
                        <span className="ml-2 text-muted">{item.symbol}</span>
                      </span>
                      <span className="text-muted">{item.current_price > 0 ? `${item.current_price.toLocaleString("ko-KR")}원` : "-"}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Selected chips */}
          {selectedSymbols.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {selectedSymbols.map((s) => (
                <span
                  key={s.symbol}
                  className="flex items-center gap-1.5 rounded-full border border-accent bg-accentSoft px-3 py-1 text-sm font-semibold text-accent"
                >
                  {s.name}
                  <span className="text-xs font-normal text-muted">{s.symbol}</span>
                  <button
                    className="ml-1 text-muted hover:text-coral"
                    onClick={() => removeSymbol(s.symbol)}
                    type="button"
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Date range + capital */}
        <div className="mt-5 grid gap-4 md:grid-cols-3">
          <Input label="시작일" type="date" value={startDate} max={today(-1)} onChange={(e) => setStartDate(e.target.value)} />
          <Input label="종료일" type="date" value={endDate} max={today(-1)} onChange={(e) => setEndDate(e.target.value)} />
          <Input label="초기 자본" type="number" value={capital} onChange={(e) => setCapital(e.target.value)} />
        </div>

        {/* Strategy selection */}
        <div className="mt-4 space-y-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-muted">테스트 전략</span>
            <select
              className="w-full rounded-md border border-line bg-white px-3 py-3 text-text outline-none transition focus:border-accent focus:ring-2 focus:ring-accentSoft"
              onChange={(event) => setStrategyId(event.target.value)}
              value={strategyId}
            >
              {allStrategies.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.label}
                </option>
              ))}
            </select>
          </label>
          <p className="rounded-md border border-line bg-white px-4 py-3 text-sm leading-6 text-muted">
            {selectedStrategy?.description ?? "선택한 전략 설명이 없습니다."}
          </p>
        </div>

        <div className="mt-5 space-y-3 rounded-md border border-line bg-background/70 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-text">필터</p>
              <p className="mt-1 text-xs text-muted">전략을 바꾸면 권장값으로 초기화됩니다.</p>
            </div>
            <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
              전략별 추천값 자동 세팅
            </span>
          </div>
          <div className="grid gap-4 md:grid-cols-4">
            <label className="block">
              <span className="mb-2 block">
                <FilterToggle checked={useTrendFilter} label="추세 필터 사용" onChange={setUseTrendFilter} />
              </span>
              <select
                className="w-full rounded-md border border-line bg-white px-3 py-3 text-text outline-none transition focus:border-accent focus:ring-2 focus:ring-accentSoft disabled:bg-background disabled:text-muted"
                disabled={!useTrendFilter}
                onChange={(event) => setTrendFilter(event.target.value as TrendFilter)}
                value={trendFilter}
              >
                {TREND_FILTER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="space-y-4 md:col-span-2">
              <span className="mb-2 block">
                <FilterToggle checked={useRsiFilter} label="RSI 필터 사용" onChange={setUseRsiFilter} />
              </span>
              <div className="grid gap-4 md:grid-cols-2">
                <Input
                  className={!useRsiFilter ? "bg-background text-muted" : ""}
                  disabled={!useRsiFilter}
                  label="RSI 최소값"
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={rsiMin}
                  onChange={(e) => setRsiMin(e.target.value)}
                />
                <Input
                  className={!useRsiFilter ? "bg-background text-muted" : ""}
                  disabled={!useRsiFilter}
                  label="RSI 최대값"
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={rsiMax}
                  onChange={(e) => setRsiMax(e.target.value)}
                />
              </div>
            </div>
            <div>
              <span className="mb-2 block">
                <FilterToggle checked={useVolumeFilter} label="거래량 필터 사용" onChange={setUseVolumeFilter} />
              </span>
              <Input
                className={!useVolumeFilter ? "bg-background text-muted" : ""}
                disabled={!useVolumeFilter}
                label="최소 거래량 비율"
                type="number"
                min="0"
                step="0.05"
                value={minVolumeRatio}
                onChange={(e) => setMinVolumeRatio(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="mt-4">
          <Button onClick={run} disabled={loading}>
            {loading ? "실행 중" : "전략 테스트 실행"}
          </Button>
        </div>
        {loading && <LoadingBar active label="선택 종목에 전략 테스트를 실행하고 있습니다." />}
        {error && (
          <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{error}</p>
        )}
      </section>

      {result && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Metric label="선택 종목" value={`${selectedSymbols.length}개`} />
            <Metric label="실행 전략" value={result.strategy_runs[0]?.strategy.label ?? "-"} />
            <Metric
              label="테스트 기간"
              value={`${startDate} ~ ${endDate}`}
              tone="text-accent"
            />
          </div>

          <NotesList notes={result.notes} />

          {result.strategy_runs.length > 0 ? (
            <StrategyResults runs={result.strategy_runs} />
          ) : (
            <div className="rounded-md border border-line bg-white px-4 py-6 text-center text-sm text-muted">
              <p>실행 가능한 전략 결과가 없습니다.</p>
              <p className="mt-2 text-xs text-muted">
                필터를 켠 경우 조건이 너무 좁아서 종목이 모두 제외됐을 수 있습니다.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
