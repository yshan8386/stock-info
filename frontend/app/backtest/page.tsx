"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type { AutoBacktestResult, BacktestResult, StrategyBacktestRun, StrategyInfo } from "@/types/api";

const currency = new Intl.NumberFormat("ko-KR");
const percent = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 });
const DEFAULT_STRATEGIES: StrategyInfo[] = [
  {
    id: "pullback_rebound_v1",
    label: "눌림목 반등",
    description: "상승 추세에서 눌림 이후 반등하는 종목을 추적합니다."
  },
  {
    id: "support_resistance_v1",
    label: "지지·저항 돌파",
    description: "지지선 반등과 저항선 돌파 신호를 이용해 추세 지속 구간을 추적합니다."
  }
];

function formatMarketCap(value: number): string {
  const trillion = 1_000_000_000_000;
  const billion = 100_000_000;
  if (value >= trillion) return `${(value / trillion).toFixed(0)}조원`;
  if (value >= billion) return `${(value / billion).toFixed(0)}억원`;
  return `${currency.format(Math.round(value))}원`;
}

function equityPolyline(result: BacktestResult | null): string {
  const points = result?.equity_curve ?? [];
  if (points.length === 0) return "";
  const values = points.map((point) => point.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 100;
      const y = 60 - ((point.equity - min) / span) * 52 - 4;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function today(offsetDays = 0): string {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
}

function parsePositiveNumber(value: string, label: string): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${label}은 0보다 큰 숫자로 입력하세요.`);
  }
  return parsed;
}

export default function BacktestPage() {
  const [startDate, setStartDate] = useState(today(-180));
  const [endDate, setEndDate] = useState(today());
  const [initialCapital, setInitialCapital] = useState("10000000");
  const [maxSymbols, setMaxSymbols] = useState("50");
  const [strategies, setStrategies] = useState<StrategyInfo[]>(DEFAULT_STRATEGIES);
  const [selectedStrategyIds, setSelectedStrategyIds] = useState<string[]>(DEFAULT_STRATEGIES.map((strategy) => strategy.id));
  const [result, setResult] = useState<AutoBacktestResult | null>(null);
  const [activeStrategyId, setActiveStrategyId] = useState<string | null>(DEFAULT_STRATEGIES[0]?.id ?? null);
  const [activeSymbol, setActiveSymbol] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<StrategyInfo[]>("/backtest/strategies")
      .then((data) => {
        if (!data.length) return;
        setStrategies(data);
        setSelectedStrategyIds((current) => current.length ? current.filter((id) => data.some((strategy) => strategy.id === id)) : data.map((strategy) => strategy.id));
        setActiveStrategyId((current) => current && data.some((strategy) => strategy.id === current) ? current : data[0].id);
      })
      .catch(() => {
        setStrategies(DEFAULT_STRATEGIES);
        setSelectedStrategyIds(DEFAULT_STRATEGIES.map((strategy) => strategy.id));
        setActiveStrategyId(DEFAULT_STRATEGIES[0]?.id ?? null);
      });
  }, []);

  const activeRun = useMemo<StrategyBacktestRun | null>(() => {
    if (!result) return null;
    return result.strategy_runs.find((run) => run.strategy.id === activeStrategyId) ?? result.strategy_runs[0] ?? null;
  }, [activeStrategyId, result]);
  const activeResult = useMemo(() => {
    if (!activeRun) return null;
    return activeRun.results.find((item) => item.symbol === activeSymbol) ?? activeRun.results[0] ?? null;
  }, [activeRun, activeSymbol]);
  const polyline = equityPolyline(activeResult);

  async function run() {
    setError(null);
    let parsedInitialCapital: number;
    let parsedMaxSymbols: number;
    try {
      if (!startDate || !endDate) throw new Error("시작일과 종료일을 모두 입력하세요.");
      if (startDate >= endDate) throw new Error("종료일은 시작일보다 뒤여야 합니다.");
      parsedInitialCapital = parsePositiveNumber(initialCapital, "초기 자본");
      parsedMaxSymbols = parsePositiveNumber(maxSymbols, "비교 종목 수");
      if (parsedMaxSymbols > 50) throw new Error("비교 종목 수는 50개 이하로 입력하세요.");
      if (!selectedStrategyIds.length) throw new Error("최소 1개 전략을 선택하세요.");
    } catch (exc) {
      setResult(null);
      setActiveStrategyId(null);
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
          initial_capital: parsedInitialCapital,
          max_symbols: parsedMaxSymbols,
          strategy_ids: selectedStrategyIds
        })
      });
      setResult(data);
      setActiveStrategyId(data.strategy_runs[0]?.strategy.id ?? null);
      setActiveSymbol(data.strategy_runs[0]?.results[0]?.symbol ?? null);
    } catch (exc) {
      setResult(null);
      setActiveStrategyId(null);
      setActiveSymbol(null);
      setError(exc instanceof Error ? exc.message : "백테스트 실행에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="font-backtest space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-accent">자동 종목선정</p>
          <h1 className="mt-1 text-3xl font-bold">백테스트</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            동일한 종목군에 여러 전략을 동시에 실행해서 수익률과 MDD를 비교합니다. 공통 종목군은 시가총액과 전일 거래량 종합 순위로 고릅니다.
          </p>
        </div>
        <Button onClick={run} disabled={loading}>
          {loading ? "실행 중" : "백테스트 실행"}
        </Button>
      </div>

      <section className="surface rounded-md p-5">
        <div className="grid gap-4 md:grid-cols-4">
          <Input label="시작일" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
          <Input label="종료일" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
          <Input label="초기 자본" type="number" value={initialCapital} onChange={(event) => setInitialCapital(event.target.value)} />
          <Input label="비교 종목 수" type="number" value={maxSymbols} onChange={(event) => setMaxSymbols(event.target.value)} />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {strategies.map((strategy) => {
            const checked = selectedStrategyIds.includes(strategy.id);
            const isOnlySelected = checked && selectedStrategyIds.length === 1;
            return (
              <label key={strategy.id} className={`rounded-md border bg-white p-4 transition ${checked ? "border-accent bg-accentSoft" : "border-line"}`}>
                <span className="flex items-start gap-3">
                  <input
                    checked={checked}
                    className="mt-1 h-4 w-4 accent-[#0f8a65]"
                    disabled={isOnlySelected}
                    onChange={() => {
                      setSelectedStrategyIds((current) =>
                        checked ? current.filter((item) => item !== strategy.id) : [...current, strategy.id]
                      );
                    }}
                    type="checkbox"
                  />
                  <span>
                    <span className="block text-sm font-semibold text-text">{strategy.label}</span>
                    <span className="mt-1 block text-sm leading-6 text-muted">{strategy.description}</span>
                  </span>
                </span>
              </label>
            );
          })}
        </div>
        {loading ? <LoadingBar active label="공통 종목선정과 전략 비교 백테스트를 실행 중입니다." /> : null}
        {error ? <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{error}</p> : null}
      </section>

      {result ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Metric label="선정 종목" value={`${result.selected.length}개`} />
            <Metric label="비교 전략" value={`${result.strategy_runs.length}개`} />
            <Metric
              label="기준 전략"
              value={activeRun?.strategy.label ?? "-"}
              tone="text-accent"
            />
            <Metric label="선택 종목 상세" value={activeResult?.symbol_name ?? "-"} />
          </div>

          {result.notes.length > 0 ? (
            <section className="surface rounded-md p-5">
              <h2 className="text-xl font-bold">실행 메모</h2>
              <ul className="mt-3 grid gap-2 text-sm leading-6 text-muted">
                {result.notes.map((note) => (
                  <li key={note} className="rounded-md border border-line bg-white px-4 py-3">
                    {note}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="surface rounded-md p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">전략 비교</h2>
                <p className="mt-1 text-sm text-muted">같은 종목군에 같은 예산을 나눠서 전략별 성과를 비교합니다.</p>
              </div>
              <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
                공통 종목군 {result.request.max_symbols}개
              </span>
            </div>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {result.strategy_runs.map((run) => (
                <button
                  key={run.strategy.id}
                  className={`rounded-md border p-4 text-left transition ${
                    activeRun?.strategy.id === run.strategy.id ? "border-accent bg-accentSoft" : "border-line bg-white hover:border-accent"
                  }`}
                  onClick={() => {
                    setActiveStrategyId(run.strategy.id);
                    setActiveSymbol(run.results[0]?.symbol ?? null);
                  }}
                  type="button"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-bold">{run.strategy.label}</p>
                      <p className="mt-1 text-sm leading-6 text-muted">{run.strategy.description}</p>
                    </div>
                    <Icon name="arrowRight" className="h-4 w-4 text-muted" />
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-4">
                    <SummaryPill label="수익률" value={`${percent.format(run.summary.total_return_pct)}%`} tone={run.summary.total_return_pct >= 0 ? "text-accent" : "text-coral"} />
                    <SummaryPill label="MDD" value={`${percent.format(run.summary.max_drawdown_pct)}%`} />
                    <SummaryPill label="승률" value={`${percent.format(run.summary.win_rate_pct)}%`} />
                    <SummaryPill label="거래" value={`${run.summary.trade_count}회`} />
                  </div>
                </button>
              ))}
            </div>
          </section>

          <section className="surface rounded-md p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold">선정 종목</h2>
              <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
                시총 + 전일 거래량 종합 점수
              </span>
            </div>
            {result.selected.length > 0 ? (
              <div className="mt-4 grid gap-3 lg:grid-cols-5">
                {result.selected.map((item) => (
                  <button
                    key={item.symbol}
                    className={`rounded-md border p-4 text-left transition ${
                      activeResult?.symbol === item.symbol ? "border-accent bg-accentSoft" : "border-line bg-white hover:border-accent"
                    }`}
                    onClick={() => setActiveSymbol(item.symbol)}
                    type="button"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-bold">{item.name}</p>
                      <Icon name="arrowRight" className="h-4 w-4 text-muted" />
                    </div>
                    <p className="mt-1 text-xs text-muted">{item.symbol}</p>
                    <p className="mt-3 text-sm text-muted">현재가</p>
                    <p className="font-semibold">{currency.format(Math.round(item.current_price))}원</p>
                    <p className="mt-2 text-sm text-muted">배정예산</p>
                    <p className="font-semibold">{currency.format(Math.round(item.allocated_budget ?? 0))}원</p>
                    <p className="mt-2 text-xs text-muted">매수 가능 {item.max_buyable_quantity ?? 0}주 · 점수 {item.score}</p>
                    <p className="mt-3 text-sm text-muted">평균 거래대금</p>
                    <p className="font-semibold">{currency.format(Math.round(item.avg_trade_amount))}원</p>
                    {item.market_cap != null ? (
                      <>
                        <p className="mt-2 text-sm text-muted">시가총액</p>
                        <p className="font-semibold">{formatMarketCap(item.market_cap)}</p>
                      </>
                    ) : null}
                  </button>
                ))}
              </div>
            ) : (
              <p className="mt-4 rounded-md border border-line bg-white px-4 py-3 text-sm text-muted">
                조건을 통과한 종목이 없습니다. 거래대금 기준선을 낮추거나 초기 자본을 늘려 다시 실행하세요.
              </p>
            )}
          </section>

          {activeResult ? (
            <>
              <section className="surface rounded-md p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-info">{activeRun?.strategy.label}</p>
                    <p className="text-sm font-semibold text-accent">
                      {activeResult.symbol_name} · {activeResult.symbol}
                    </p>
                    <h2 className="text-xl font-bold">종목별 결과</h2>
                  </div>
                  <span className="rounded-md bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">
                    수익률 {percent.format(activeResult.metrics.total_return_pct)}%
                  </span>
                </div>
                {polyline ? (
                  <svg className="mt-4 h-52 w-full overflow-visible rounded-md bg-white" viewBox="0 0 100 60" preserveAspectRatio="none">
                    <polyline points={polyline} fill="none" stroke="#10865f" strokeWidth="1.8" vectorEffect="non-scaling-stroke" />
                  </svg>
                ) : (
                  <p className="mt-4 rounded-md border border-line bg-white px-4 py-10 text-center text-sm text-muted">
                    표시할 자본 곡선 데이터가 없습니다.
                  </p>
                )}
              </section>

              <div className="grid gap-4 lg:grid-cols-2">
                <LevelList title="지지선 기준 금액" levels={activeResult.supports} />
                <LevelList title="저항선 기준 금액" levels={activeResult.resistances} />
              </div>

              <section className="surface overflow-hidden rounded-md">
                <div className="border-b border-line p-5">
                  <h2 className="text-xl font-bold">거래 내역</h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px] text-left text-sm">
                    <thead className="bg-background text-muted">
                      <tr>
                        <th className="px-4 py-3">진입가</th>
                        <th className="px-4 py-3">사유</th>
                        <th className="px-4 py-3">손절 기준</th>
                        <th className="px-4 py-3">익절 기준</th>
                        <th className="px-4 py-3">청산</th>
                        <th className="px-4 py-3">손익</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeResult.trades.length > 0 ? (
                        activeResult.trades.map((trade) => (
                          <tr key={`${trade.entry_at}-${trade.entry_price}`} className="border-t border-line">
                            <td className="px-4 py-3">{currency.format(trade.entry_price)}</td>
                            <td className="px-4 py-3">{trade.reason}</td>
                            <td className="px-4 py-3">{currency.format(trade.stop_loss)}</td>
                            <td className="px-4 py-3">{currency.format(trade.take_profit)}</td>
                            <td className="px-4 py-3">{trade.exit_price ? `${currency.format(trade.exit_price)} (${trade.exit_reason})` : "-"}</td>
                            <td className={`px-4 py-3 font-semibold ${(trade.pnl ?? 0) >= 0 ? "text-accent" : "text-coral"}`}>
                              {trade.pnl === null ? "-" : `${currency.format(Math.round(trade.pnl))}원`}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr className="border-t border-line">
                          <td className="px-4 py-6 text-center text-muted" colSpan={6}>
                            조건에 맞는 매매 신호가 없어 거래 내역이 없습니다.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function Metric({ label, value, tone = "text-text" }: { label: string; value: string; tone?: string }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className={`mt-2 break-words text-2xl font-bold ${tone}`}>{value}</p>
    </Card>
  );
}

function SummaryPill({ label, value, tone = "text-text" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${tone}`}>{value}</p>
    </div>
  );
}

function LevelList({ title, levels }: { title: string; levels: BacktestResult["supports"] }) {
  return (
    <section className="surface rounded-md p-5">
      <h2 className="text-xl font-bold">{title}</h2>
      <div className="mt-4 grid gap-2">
        {levels.length > 0 ? (
          levels.map((level) => (
            <div key={`${level.kind}-${level.price}`} className="flex items-center justify-between gap-3 rounded-md border border-line bg-white px-4 py-3 text-sm">
              <span className="font-semibold">{currency.format(level.price)}원</span>
              <span className="text-muted">강도 {percent.format(level.strength * 100)} · 터치 {level.touches}</span>
            </div>
          ))
        ) : (
          <p className="rounded-md border border-line bg-white px-4 py-3 text-sm text-muted">감지된 기준 금액이 없습니다.</p>
        )}
      </div>
    </section>
  );
}
