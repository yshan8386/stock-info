"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type { AutoBacktestResult, SelectedSymbol, StrategyInfo } from "@/types/api";
import { Metric, NotesList, StockSelectionGrid, StrategyResults } from "./_shared";
import { SelectionTab } from "./SelectionTab";
import { StrategyOnlyTab } from "./StrategyOnlyTab";

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

type Tab = "combined" | "selection" | "strategy";

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

export default function BacktestPage() {
  const [activeTab, setActiveTab] = useState<Tab>("combined");
  const [strategies, setStrategies] = useState<StrategyInfo[]>(DEFAULT_STRATEGIES);
  const [preloadedStocks, setPreloadedStocks] = useState<SelectedSymbol[] | null>(null);

  // Combined tab state
  const [startDate, setStartDate] = useState(today(-180));
  const [endDate, setEndDate] = useState(today());
  const [initialCapital, setInitialCapital] = useState("2000000");
  const [maxSymbols, setMaxSymbols] = useState("4");
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>(DEFAULT_STRATEGIES[0].id);
  const [result, setResult] = useState<AutoBacktestResult | null>(null);
  const [activeSymbol, setActiveSymbol] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<StrategyInfo[]>("/backtest/strategies")
      .then((data) => {
        if (!data.length) return;
        setStrategies(data);
        setSelectedStrategyId((curr) => (data.some((s) => s.id === curr) ? curr : data[0].id));
      })
      .catch(() => {
        setStrategies(DEFAULT_STRATEGIES);
        setSelectedStrategyId((curr) =>
          DEFAULT_STRATEGIES.some((s) => s.id === curr) ? curr : DEFAULT_STRATEGIES[0].id
        );
      });
  }, []);

  const activeRun = useMemo(() => {
    if (!result) return null;
    return result.strategy_runs[0] ?? null;
  }, [result]);

  const activeResult = useMemo(() => {
    if (!activeRun) return null;
    return activeRun.results.find((r) => r.symbol === activeSymbol) ?? activeRun.results[0] ?? null;
  }, [activeRun, activeSymbol]);

  async function runCombined() {
    setError(null);
    let parsedCapital: number;
    let parsedMax: number;
    try {
      if (!startDate || !endDate) throw new Error("시작일과 종료일을 모두 입력하세요.");
      if (startDate >= endDate) throw new Error("종료일은 시작일보다 뒤여야 합니다.");
      parsedCapital = parsePositiveNumber(initialCapital, "초기 자본");
      parsedMax = parsePositiveNumber(maxSymbols, "비교 종목 수");
      if (parsedMax > 50) throw new Error("비교 종목 수는 50개 이하로 입력하세요.");
      if (!selectedStrategyId) throw new Error("전략을 선택하세요.");
    } catch (exc) {
      setResult(null);
      setActiveSymbol(null);
      setError(exc instanceof Error ? exc.message : "입력값을 확인하세요.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch<AutoBacktestResult>("/backtest/run", {
        method: "POST",
        body: JSON.stringify({
          start_date: startDate,
          end_date: endDate,
          initial_capital: parsedCapital,
          max_symbols: parsedMax,
          strategy_ids: [selectedStrategyId],
        }),
      });
      setResult(data);
      setActiveSymbol(data.strategy_runs[0]?.results[0]?.symbol ?? null);
    } catch (exc) {
      setResult(null);
      setActiveSymbol(null);
      setError(exc instanceof Error ? exc.message : "백테스트 실행에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  function handleGoToStrategy(stocks: SelectedSymbol[]) {
    setPreloadedStocks(stocks);
    setActiveTab("strategy");
  }

  const tabs: { id: Tab; label: string; desc: string }[] = [
    { id: "combined", label: "종목선정 + 전략", desc: "자동 종목선정 후 전략 테스트" },
    { id: "selection", label: "종목선정만", desc: "기준일 기준 종목 스크리닝" },
    { id: "strategy", label: "전략 테스트", desc: "직접 선택한 종목에 전략 적용" },
  ];

  const strategyOptions = strategies.length ? strategies : DEFAULT_STRATEGIES;
  const selectedStrategy = strategyOptions.find((strategy) => strategy.id === selectedStrategyId) ?? strategyOptions[0];

  return (
    <div className="font-backtest space-y-6">
      <div>
        <h1 className="text-3xl font-bold">백테스트</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          종목선정과 전략 시뮬레이션을 단계별로 또는 통합해서 실행할 수 있습니다.
        </p>
      </div>

      {/* Tab nav */}
      <div className="flex gap-1 rounded-lg border border-line bg-background p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`flex-1 rounded-md px-4 py-2.5 text-sm transition ${
              activeTab === tab.id
                ? "bg-white font-semibold text-text shadow-sm"
                : "text-muted hover:text-text"
            }`}
            onClick={() => setActiveTab(tab.id)}
            type="button"
          >
            <span className="block">{tab.label}</span>
            <span className="mt-0.5 block text-xs font-normal text-muted">{tab.desc}</span>
          </button>
        ))}
      </div>

      {activeTab === "selection" && (
        <SelectionTab onGoToStrategy={handleGoToStrategy} />
      )}

      {activeTab === "strategy" && (
        <StrategyOnlyTab strategies={strategies} preloadedStocks={preloadedStocks} />
      )}

      {activeTab === "combined" && (
        <div className="space-y-6">
          <section className="surface rounded-md p-5">
            <p className="text-sm font-semibold text-accent">자동 종목선정 + 전략 테스트</p>
            <p className="mt-1 text-sm leading-6 text-muted">
              기준일(매매 시작일) 이전 데이터로 종목을 선정하고, 기준일부터 종료일까지 전략을 시뮬레이션합니다.
            </p>
            <div className="mt-4 grid gap-4 md:grid-cols-4">
              <Input label="기준일 (매매 시작일)" type="date" value={startDate} max={today(-1)} onChange={(e) => setStartDate(e.target.value)} />
              <Input label="종료일" type="date" value={endDate} max={today(-1)} onChange={(e) => setEndDate(e.target.value)} />
              <Input label="초기 자본" type="number" value={initialCapital} onChange={(e) => setInitialCapital(e.target.value)} />
              <Input label="비교 종목 수" type="number" value={maxSymbols} onChange={(e) => setMaxSymbols(e.target.value)} />
            </div>
            <div className="mt-4 space-y-2">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-muted">테스트 전략</span>
                <select
                  className="w-full rounded-md border border-line bg-white px-3 py-3 text-text outline-none transition focus:border-accent focus:ring-2 focus:ring-accentSoft"
                  onChange={(event) => setSelectedStrategyId(event.target.value)}
                  value={selectedStrategyId}
                >
                  {strategyOptions.map((strategy) => (
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
            <div className="mt-4">
              <Button onClick={runCombined} disabled={loading}>
                {loading ? "실행 중" : "전략 테스트 실행"}
              </Button>
            </div>
            {loading && <LoadingBar active label="공통 종목선정 후 선택한 전략 테스트를 실행 중입니다." />}
            {error && (
              <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{error}</p>
            )}
          </section>

          {result && (
            <>
              <div className="grid gap-4 md:grid-cols-4">
                <Metric label="선정 종목" value={`${result.selected.length}개`} />
                <Metric label="실행 전략" value={activeRun?.strategy.label ?? "-"} tone="text-accent" />
                <Metric label="테스트 기간" value={`${startDate} ~ ${endDate}`} />
                <Metric label="선택 종목" value={activeResult?.symbol_name ?? "-"} />
              </div>

              <NotesList notes={result.notes} />

              <section className="surface rounded-md p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h2 className="text-xl font-bold">선정 종목</h2>
                  <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
                    시총 우선 + 주가 상한 + 최근 과열 제외
                  </span>
                </div>
                <StockSelectionGrid
                  selected={result.selected}
                  activeSymbol={activeSymbol}
                  onSymbolClick={setActiveSymbol}
                />
              </section>

              <StrategyResults
                runs={result.strategy_runs}
                initialStrategyId={result.strategy_runs[0]?.strategy.id}
                initialSymbol={result.strategy_runs[0]?.results[0]?.symbol}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
}
