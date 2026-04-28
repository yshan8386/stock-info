"use client";

import { useMemo, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import type { BacktestResult, BenchmarkPoint, StockSelectionItem, StrategyBacktestRun } from "@/types/api";

export const currency = new Intl.NumberFormat("ko-KR");
export const percent = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 });
const RESULT_CHART_WIDTH = 100;
const RESULT_CHART_HEIGHT = 20;
const RESULT_CHART_VERTICAL_PADDING = 2;
const RESULT_CHART_DRAW_HEIGHT = 16;
const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

function formatTradeDate(value: string | null | undefined): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return dateFormatter.format(date).replace(/\. /g, "-").replace(".", "");
}

function formatRatio(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "-";
  return percent.format(value);
}

function mapTradeReason(reason: string | null | undefined): string {
  switch (reason) {
    case "pullback_rebound":
      return "눌림목 반등 진입";
    case "support_bounce":
      return "지지선 반등 진입";
    case "resistance_breakout":
      return "저항 돌파 진입";
    case "stop_loss":
      return "손절";
    case "take_profit":
      return "익절";
    case "slope_reversal":
      return "기울기 반전 청산";
    case "support_breakdown":
      return "지지선 이탈 청산";
    case "short_ma_break":
      return "단기 이평 이탈 청산";
    case "trend_break":
      return "추세 훼손 청산";
    case "end_of_data":
      return "기간 종료 청산";
    default:
      return reason ?? "-";
  }
}

export function formatMarketCap(value: number): string {
  const trillion = 1_000_000_000_000;
  const billion = 100_000_000;
  if (value >= trillion) return `${(value / trillion).toFixed(0)}조원`;
  if (value >= billion) return `${(value / billion).toFixed(0)}억원`;
  return `${currency.format(Math.round(value))}원`;
}

type SeriesPoint = {
  timestamp: string;
  close: number;
};

type ChartPoint = {
  timestamp: string;
  x: number;
  y: number;
};

function getNormalizedSeries(points: SeriesPoint[]) {
  if (!points.length) return [];
  const base = points[0].close;
  if (!base) return [];
  return points.map((point) => ({
    timestamp: point.timestamp,
    value: ((point.close / base) - 1) * 100,
  }));
}

function buildComparisonChart(result: BacktestResult | null, benchmark: BenchmarkPoint[]) {
  const stockSeries = getNormalizedSeries(
    (result?.equity_curve ?? []).map((point) => ({
      timestamp: point.timestamp,
      close: point.close,
    }))
  );
  const benchmarkSeries = getNormalizedSeries(
    benchmark.map((point) => ({
      timestamp: point.timestamp,
      close: point.close,
    }))
  );

  if (stockSeries.length === 0) {
    return null;
  }

  const allSeries = [...stockSeries, ...benchmarkSeries];
  const allTimes = allSeries.map((point) => new Date(point.timestamp).getTime()).filter((value) => !Number.isNaN(value));
  if (!allTimes.length) {
    return null;
  }

  const minTime = Math.min(...allTimes);
  const maxTime = Math.max(...allTimes);
  const timeSpan = Math.max(maxTime - minTime, 1);
  const allValues = allSeries.map((point) => point.value);
  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);
  const valueSpan = maxValue - minValue || 1;

  const toChartPoints = (series: typeof stockSeries): ChartPoint[] =>
    series.map((point) => {
      const pointTime = new Date(point.timestamp).getTime();
      const x = ((pointTime - minTime) / timeSpan) * RESULT_CHART_WIDTH;
      const y =
        RESULT_CHART_HEIGHT -
        ((point.value - minValue) / valueSpan) * RESULT_CHART_DRAW_HEIGHT -
        RESULT_CHART_VERTICAL_PADDING;
      return { timestamp: point.timestamp, x, y };
    });

  const stockPoints = toChartPoints(stockSeries);
  const benchmarkPoints = toChartPoints(benchmarkSeries);

  return {
    stockPolyline: stockPoints.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" "),
    benchmarkPolyline: benchmarkPoints.map((point) => `${point.x.toFixed(2)},${point.y.toFixed(2)}`).join(" "),
    stockPoints,
    hasBenchmark: benchmarkPoints.length > 0,
  };
}

function findNearestCurveIndex(points: Array<{ timestamp: string }>, targetTimestamp: string): number | null {
  if (!points.length) return null;
  const targetMs = new Date(targetTimestamp).getTime();
  if (Number.isNaN(targetMs)) return null;

  let nearestIndex = 0;
  let nearestDistance = Number.POSITIVE_INFINITY;

  points.forEach((point, index) => {
    const pointMs = new Date(point.timestamp).getTime();
    if (Number.isNaN(pointMs)) return;
    const distance = Math.abs(pointMs - targetMs);
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestIndex = index;
    }
  });

  return nearestIndex;
}

function getTradeMarkers(result: BacktestResult | null, stockPoints: ChartPoint[]) {
  if (!stockPoints.length) return [];

  return (result?.trades ?? []).flatMap((trade, tradeIndex) => {
    const markers: Array<{
      key: string;
      kind: "buy" | "sell";
      x: number;
      y: number;
      label: string;
      title: string;
    }> = [];

    const entryIndex = findNearestCurveIndex(stockPoints, trade.entry_at);
    if (entryIndex != null) {
      const position = stockPoints[entryIndex];
      markers.push({
        key: `buy-${tradeIndex}-${trade.entry_at}`,
        kind: "buy",
        x: position.x,
        y: position.y,
        label: "매수",
        title: [
          `매수 · ${formatTradeDate(trade.entry_at)}`,
          `가격: ${currency.format(Math.round(trade.entry_price))}원`,
          `RSI: ${formatRatio(trade.entry_rsi)}`,
          `거래량비율: ${formatRatio(trade.entry_volume_ratio)}배`,
        ].join("\n"),
      });
    }

    if (trade.exit_at && trade.exit_price != null) {
      const exitIndex = findNearestCurveIndex(stockPoints, trade.exit_at);
      if (exitIndex != null) {
        const position = stockPoints[exitIndex];
        markers.push({
          key: `sell-${tradeIndex}-${trade.exit_at}`,
          kind: "sell",
          x: position.x,
          y: position.y,
          label: "매도",
          title: [
            `매도 · ${formatTradeDate(trade.exit_at)}`,
            `가격: ${currency.format(Math.round(trade.exit_price))}원`,
            `RSI: ${formatRatio(trade.exit_rsi)}`,
            `거래량비율: ${formatRatio(trade.exit_volume_ratio)}배`,
          ].join("\n"),
        });
      }
    }

    return markers;
  });
}

type TradeSummary = {
  buyCount: number;
  sellCount: number;
  buyAmount: number;
  sellAmount: number;
};

function summarizeTrades(trades: BacktestResult["trades"]): TradeSummary {
  const buyCount = trades.length;
  const sellTrades = trades.filter((trade) => trade.exit_price != null);
  const sellCount = sellTrades.length;
  const buyAmount = trades.reduce((sum, trade) => sum + trade.entry_price * trade.quantity, 0);
  const sellAmount = sellTrades.reduce(
    (sum, trade) => sum + (trade.exit_price ?? 0) * trade.quantity,
    0
  );

  return {
    buyCount,
    sellCount,
    buyAmount,
    sellAmount,
  };
}

function getTradeSummary(result: BacktestResult | null): TradeSummary {
  return summarizeTrades(result?.trades ?? []);
}

function getRunTradeSummary(run: StrategyBacktestRun | null): TradeSummary {
  const trades = run?.results.flatMap((result) => result.trades) ?? [];
  return summarizeTrades(trades);
}

export function Metric({ label, value, tone = "text-text" }: { label: string; value: string; tone?: string }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className={`mt-2 break-words text-2xl font-bold ${tone}`}>{value}</p>
    </Card>
  );
}

export function SummaryPill({ label, value, tone = "text-text" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-md border border-line bg-panel px-3 py-2">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${tone}`}>{value}</p>
    </div>
  );
}

export function LevelList({ title, levels }: { title: string; levels: BacktestResult["supports"] }) {
  return (
    <section className="surface rounded-md p-5">
      <h2 className="text-xl font-bold">{title}</h2>
      <div className="mt-4 grid gap-2">
        {levels.length > 0 ? (
          levels.map((level) => (
            <div
              key={`${level.kind}-${level.price}`}
              className="flex items-center justify-between gap-3 rounded-md border border-line bg-white px-4 py-3 text-sm"
            >
              <span className="font-semibold">{currency.format(level.price)}원</span>
              <span className="text-muted">강도 {percent.format(level.strength * 100)} · 터치 {level.touches}</span>
            </div>
          ))
        ) : (
          <p className="rounded-md border border-line bg-white px-4 py-3 text-sm text-muted">
            감지된 기준 금액이 없습니다.
          </p>
        )}
      </div>
    </section>
  );
}

export function NotesList({ notes }: { notes: string[] }) {
  if (!notes.length) return null;
  return (
    <section className="surface rounded-md p-5">
      <h2 className="text-xl font-bold">실행 메모</h2>
      <ul className="mt-3 grid gap-2 text-sm leading-6 text-muted">
        {notes.map((note) => (
          <li key={note} className="rounded-md border border-line bg-white px-4 py-3">
            {note}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function StockSelectionGrid({
  selected,
  activeSymbol,
  onSymbolClick,
}: {
  selected: StockSelectionItem[];
  activeSymbol?: string | null;
  onSymbolClick?: (symbol: string) => void;
}) {
  if (selected.length === 0) {
    return (
      <p className="mt-4 rounded-md border border-line bg-white px-4 py-3 text-sm text-muted">
        조건을 통과한 종목이 없습니다.
      </p>
    );
  }
  return (
    <div className="mt-4 grid gap-3 lg:grid-cols-5">
      {selected.map((item) => (
        <button
          key={item.symbol}
          className={`rounded-md border p-4 text-left transition ${
            activeSymbol === item.symbol ? "border-accent bg-accentSoft" : "border-line bg-white hover:border-accent"
          } ${onSymbolClick ? "cursor-pointer" : "cursor-default"}`}
          onClick={() => onSymbolClick?.(item.symbol)}
          type="button"
        >
          <div className="flex items-center justify-between gap-2">
            <p className="font-bold">{item.name}</p>
            {onSymbolClick && <Icon name="arrowRight" className="h-4 w-4 text-muted" />}
          </div>
          <p className="mt-1 text-xs text-muted">{item.symbol}</p>
          <p className="mt-3 text-sm text-muted">현재가</p>
          <p className="font-semibold">{currency.format(Math.round(item.current_price))}원</p>
          {item.allocated_budget != null && item.allocated_budget > 0 ? (
            <>
              <p className="mt-2 text-sm text-muted">배정예산</p>
              <p className="font-semibold">{currency.format(Math.round(item.allocated_budget))}원</p>
              <p className="mt-2 text-xs text-muted">
                실매수 후보 · 매수 가능 {item.max_buyable_quantity ?? 0}주 · 점수 {item.score}
              </p>
            </>
          ) : (
            <p className="mt-2 text-xs text-muted">점수 {item.score}</p>
          )}
          <p className="mt-3 text-sm text-muted">평균 거래대금</p>
          <p className="font-semibold">{currency.format(Math.round(item.avg_trade_amount))}원</p>
          <p className="mt-2 text-xs text-muted">{item.reason}</p>
          {item.market_cap != null && (
            <>
              <p className="mt-2 text-sm text-muted">시가총액</p>
              <p className="font-semibold">{formatMarketCap(item.market_cap)}</p>
            </>
          )}
        </button>
      ))}
    </div>
  );
}

export function StrategyResults({
  runs,
  initialStrategyId,
  initialSymbol,
}: {
  runs: StrategyBacktestRun[];
  initialStrategyId?: string | null;
  initialSymbol?: string | null;
}) {
  const [activeStrategyId, setActiveStrategyId] = useState<string | null>(
    initialStrategyId ?? runs[0]?.strategy.id ?? null
  );
  const [activeSymbol, setActiveSymbol] = useState<string | null>(
    initialSymbol ?? runs[0]?.results[0]?.symbol ?? null
  );

  const activeRun = useMemo(
    () => runs.find((r) => r.strategy.id === activeStrategyId) ?? runs[0] ?? null,
    [activeStrategyId, runs]
  );
  const activeResult = useMemo(
    () => activeRun?.results.find((r) => r.symbol === activeSymbol) ?? activeRun?.results[0] ?? null,
    [activeRun, activeSymbol]
  );
  const comparisonChart = useMemo(
    () => buildComparisonChart(activeResult, activeRun?.benchmark_curve ?? []),
    [activeResult, activeRun]
  );
  const runTradeSummary = useMemo(() => getRunTradeSummary(activeRun), [activeRun]);
  const tradeMarkers = useMemo(
    () => getTradeMarkers(activeResult, comparisonChart?.stockPoints ?? []),
    [activeResult, comparisonChart]
  );
  const tradeSummary = useMemo(() => getTradeSummary(activeResult), [activeResult]);

  if (!runs.length) return null;

  return (
    <>
      <section className="surface rounded-md p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">전략 테스트</h2>
            <p className="mt-1 text-sm text-muted">선택한 전략의 백테스트 성과를 종목별로 확인합니다.</p>
          </div>
        </div>
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          {runs.map((run) => (
            <button
              key={run.strategy.id}
              className={`rounded-md border p-4 text-left transition ${
                activeRun?.strategy.id === run.strategy.id
                  ? "border-accent bg-accentSoft"
                  : "border-line bg-white hover:border-accent"
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

      {activeRun && (
        <section className="surface rounded-md p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-bold">종목별 결과 선택</h2>
            <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
              {activeRun.strategy.label}
            </span>
          </div>
          <div className="mt-4 grid gap-2 md:grid-cols-4">
            {activeRun.results.map((r) => (
              <button
                key={r.symbol}
                className={`rounded-md border px-3 py-2 text-left text-sm transition ${
                  activeResult?.symbol === r.symbol ? "border-accent bg-accentSoft" : "border-line bg-white hover:border-accent"
                }`}
                onClick={() => setActiveSymbol(r.symbol)}
                type="button"
              >
                <p className="font-semibold">{r.symbol_name ?? r.symbol}</p>
                <p className={`mt-1 text-xs font-semibold ${r.metrics.total_return_pct >= 0 ? "text-accent" : "text-coral"}`}>
                  {percent.format(r.metrics.total_return_pct)}%
                </p>
              </button>
            ))}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <SummaryPill label="기간 총 매수 횟수" value={`${runTradeSummary.buyCount}회`} />
            <SummaryPill label="기간 총 매도 횟수" value={`${runTradeSummary.sellCount}회`} />
            <SummaryPill
              label="기간 총 매수 금액"
              value={`${currency.format(Math.round(runTradeSummary.buyAmount))}원`}
            />
            <SummaryPill
              label="기간 총 매도 금액"
              value={`${currency.format(Math.round(runTradeSummary.sellAmount))}원`}
            />
          </div>
        </section>
      )}

      {activeResult && (
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
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <SummaryPill label="종목 매수 횟수" value={`${tradeSummary.buyCount}회`} />
              <SummaryPill label="종목 매도 횟수" value={`${tradeSummary.sellCount}회`} />
              <SummaryPill label="종목 매수 금액" value={`${currency.format(Math.round(tradeSummary.buyAmount))}원`} />
              <SummaryPill label="종목 매도 금액" value={`${currency.format(Math.round(tradeSummary.sellAmount))}원`} />
            </div>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-text">기간 성과 비교</p>
              <p className="text-xs text-muted">종목과 코스피를 동일 시작점 대비로 비교합니다.</p>
            </div>
            {comparisonChart ? (
              <svg
                className="mt-4 h-52 w-full overflow-visible rounded-md bg-white"
                viewBox={`0 0 ${RESULT_CHART_WIDTH} ${RESULT_CHART_HEIGHT}`}
                preserveAspectRatio="none"
              >
                <polyline
                  points={comparisonChart.stockPolyline}
                  fill="none"
                  stroke="#10865f"
                  strokeWidth="1.8"
                  vectorEffect="non-scaling-stroke"
                />
                {comparisonChart.hasBenchmark && (
                  <polyline
                    points={comparisonChart.benchmarkPolyline}
                    fill="none"
                    stroke="#f59e0b"
                    strokeWidth="1.2"
                    strokeDasharray="2.2 1.4"
                    vectorEffect="non-scaling-stroke"
                  />
                )}
                {tradeMarkers.map((marker) => (
                  <g key={marker.key}>
                    <title>{marker.title}</title>
                    <circle
                      cx={marker.x}
                      cy={marker.y}
                      fill={marker.kind === "buy" ? "#205cbd" : "#d65f4b"}
                      r="0.95"
                      stroke="white"
                      strokeWidth="0.35"
                    />
                  </g>
                ))}
              </svg>
            ) : (
              <p className="mt-4 rounded-md border border-line bg-white px-4 py-10 text-center text-sm text-muted">
                표시할 비교 데이터가 없습니다.
              </p>
            )}
            {(tradeMarkers.length > 0 || comparisonChart?.hasBenchmark) && (
              <div className="mt-3 flex flex-wrap gap-4 text-xs text-muted">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-[2px] w-4 bg-[#10865f]" />
                  선택 종목
                </span>
                {comparisonChart?.hasBenchmark && (
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-[2px] w-4 border-t-2 border-dashed border-[#f59e0b]" />
                    코스피
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#205cbd]" />
                  매수 시점
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-[#d65f4b]" />
                  매도 시점
                </span>
              </div>
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
              <table className="w-full min-w-[1020px] text-left text-sm">
                <thead className="bg-background text-muted">
                  <tr>
                    <th className="px-4 py-3">진입일자</th>
                    <th className="px-4 py-3">진입가</th>
                    <th className="px-4 py-3">사유</th>
                    <th className="px-4 py-3">손절 기준</th>
                    <th className="px-4 py-3">익절 기준</th>
                    <th className="px-4 py-3">청산일자</th>
                    <th className="px-4 py-3">청산가</th>
                    <th className="px-4 py-3">청산 사유</th>
                    <th className="px-4 py-3">손익</th>
                  </tr>
                </thead>
                <tbody>
                  {activeResult.trades.length > 0 ? (
                    activeResult.trades.map((trade) => (
                      <tr key={`${trade.entry_at}-${trade.entry_price}`} className="border-t border-line">
                        <td className="px-4 py-3">{formatTradeDate(trade.entry_at)}</td>
                        <td className="px-4 py-3">{currency.format(trade.entry_price)}</td>
                        <td className="px-4 py-3">{mapTradeReason(trade.reason)}</td>
                        <td className="px-4 py-3">{currency.format(trade.stop_loss)}</td>
                        <td className="px-4 py-3">{currency.format(trade.take_profit)}</td>
                        <td className="px-4 py-3">{formatTradeDate(trade.exit_at)}</td>
                        <td className="px-4 py-3">
                          {trade.exit_price ? currency.format(trade.exit_price) : "-"}
                        </td>
                        <td className="px-4 py-3">
                          {trade.exit_reason ? mapTradeReason(trade.exit_reason) : "-"}
                        </td>
                        <td className={`px-4 py-3 font-semibold ${(trade.pnl ?? 0) >= 0 ? "text-accent" : "text-coral"}`}>
                          {trade.pnl === null ? "-" : `${currency.format(Math.round(trade.pnl))}원`}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr className="border-t border-line">
                      <td className="px-4 py-6 text-center text-muted" colSpan={9}>
                        조건에 맞는 매매 신호가 없어 거래 내역이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </>
  );
}
