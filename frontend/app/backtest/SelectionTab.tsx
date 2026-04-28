"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type {
  SelectedSymbol,
  StockDetail,
  StockSelectionDateResult,
  StockSelectionItem,
  StockSelectionRangeResult,
  StockSelectionResult,
} from "@/types/api";
import { currency, formatMarketCap, Metric, NotesList, StockSelectionGrid } from "./_shared";

type Mode = "single" | "range";

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

function daysBetween(a: string, b: string): number {
  return Math.round((new Date(b).getTime() - new Date(a).getTime()) / 86_400_000);
}

function formatDate(d: string): string {
  return d.replace(/-/g, ".");
}

function formatShortDate(d: string): string {
  return d.slice(5).replace("-", ".");
}

function formatSignedNumber(value: number | null | undefined): string {
  if (value == null) return "-";
  const rounded = Math.round(value);
  if (rounded > 0) return `+${currency.format(rounded)}`;
  return currency.format(rounded);
}

function formatSignedPercent(value: number | null | undefined): string {
  if (value == null) return "-";
  const rounded = value.toFixed(2);
  return value > 0 ? `+${rounded}%` : `${rounded}%`;
}

function formatQuantity(value: number | null | undefined, suffix: string): string {
  if (value == null) return "-";
  return `${currency.format(Math.round(value))}${suffix}`;
}

function formatRatio(value: number | null | undefined): string {
  if (value == null) return "-";
  return value.toFixed(2);
}

function formatPrice(value: number | null | undefined): string {
  if (value == null) return "-";
  return `${currency.format(Math.round(value))}원`;
}

function DetailStat({
  label,
  value,
  tone = "text-text",
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className="rounded-md border border-line bg-white px-4 py-3">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 text-sm font-semibold ${tone}`}>{value}</p>
    </div>
  );
}

function StockDetailChart({ detail }: { detail: StockDetail }) {
  const candles = detail.chart_candles;

  const chart = useMemo(() => {
    if (!candles.length) return null;

    const width = Math.max(candles.length * 8 + 56, 720);
    const height = 280;
    const padLeft = 28;
    const padRight = 18;
    const padTop = 18;
    const padBottom = 28;
    const chartHeight = height - padTop - padBottom;
    const step = (width - padLeft - padRight) / Math.max(candles.length - 1, 1);
    const candleBodyWidth = Math.max(Math.min(step * 0.58, 6), 2);
    const prices = candles.flatMap((candle) => [candle.high_price, candle.low_price]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const span = Math.max(maxPrice - minPrice, 1);
    const priceToY = (price: number) => padTop + ((maxPrice - price) / span) * chartHeight;
    const selectionIndex =
      detail.candle_date != null ? candles.findIndex((candle) => candle.candle_date === detail.candle_date) : -1;
    const latestIndex = candles.length - 1;

    return {
      width,
      height,
      padTop,
      padBottom,
      padLeft,
      padRight,
      step,
      candleBodyWidth,
      minPrice,
      maxPrice,
      priceToY,
      selectionIndex,
      latestIndex,
    };
  }, [candles, detail.candle_date]);

  if (!chart) {
    return (
      <div className="rounded-xl border border-line bg-white px-4 py-10 text-center text-sm text-muted">
        차트용 일봉 데이터를 불러오지 못했습니다.
      </div>
    );
  }

  const latest = candles[chart.latestIndex];

  return (
    <section className="rounded-xl border border-line bg-panel/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-bold">일봉 차트</h3>
          <p className="mt-1 text-sm text-muted">선정일 전후 흐름과 최신 주가 위치를 한 화면에서 비교합니다.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-accent" />
            상승봉
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-coral" />
            하락봉
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-[rgba(15,138,101,0.24)] ring-1 ring-accent" />
            선정일
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="h-2.5 w-2.5 rounded-full bg-[rgba(32,92,189,0.18)] ring-1 ring-info" />
            최신일
          </span>
        </div>
      </div>

      <div className="mt-4 overflow-x-auto rounded-xl border border-line bg-white">
        <svg
          className="block min-w-full"
          height={chart.height}
          viewBox={`0 0 ${chart.width} ${chart.height}`}
          width="100%"
        >
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const price = chart.maxPrice - (chart.maxPrice - chart.minPrice) * ratio;
            const y = chart.priceToY(price);
            return (
              <g key={ratio}>
                <line
                  stroke="rgba(23, 33, 29, 0.08)"
                  strokeDasharray="3 4"
                  x1={chart.padLeft}
                  x2={chart.width - chart.padRight}
                  y1={y}
                  y2={y}
                />
                <text
                  fill="#72807a"
                  fontSize="10"
                  textAnchor="end"
                  x={chart.padLeft - 6}
                  y={y + 3}
                >
                  {currency.format(Math.round(price))}
                </text>
              </g>
            );
          })}

          {candles.map((candle, index) => {
            const x = chart.padLeft + index * chart.step;
            const openY = chart.priceToY(candle.open_price);
            const closeY = chart.priceToY(candle.close_price);
            const highY = chart.priceToY(candle.high_price);
            const lowY = chart.priceToY(candle.low_price);
            const top = Math.min(openY, closeY);
            const bodyHeight = Math.max(Math.abs(openY - closeY), 1.5);
            const tone =
              candle.close_price > candle.open_price
                ? "#0f8a65"
                : candle.close_price < candle.open_price
                ? "#d65f4b"
                : "#7b8a83";
            const highlight =
              index === chart.selectionIndex
                ? "rgba(15, 138, 101, 0.10)"
                : index === chart.latestIndex
                ? "rgba(32, 92, 189, 0.10)"
                : null;

            return (
              <g key={candle.candle_date}>
                {highlight && (
                  <rect
                    fill={highlight}
                    height={chart.height - chart.padTop - chart.padBottom + 10}
                    rx="4"
                    width={Math.max(chart.step, 4)}
                    x={x - chart.step / 2}
                    y={chart.padTop - 5}
                  />
                )}
                <line stroke={tone} strokeWidth="1.2" x1={x} x2={x} y1={highY} y2={lowY} />
                <rect
                  fill={tone}
                  height={bodyHeight}
                  rx="1"
                  width={chart.candleBodyWidth}
                  x={x - chart.candleBodyWidth / 2}
                  y={top}
                />
              </g>
            );
          })}

          {[0, chart.selectionIndex, chart.latestIndex]
            .filter((index, position, list) => index >= 0 && list.indexOf(index) === position)
            .map((index) => {
              const candle = candles[index];
              const x = chart.padLeft + index * chart.step;
              const y = chart.priceToY(candle.close_price);
              const tone = index === chart.latestIndex ? "#205cbd" : "#0f8a65";

              return (
                <g key={`marker-${candle.candle_date}`}>
                  <circle cx={x} cy={y} fill="white" r="4.5" stroke={tone} strokeWidth="2" />
                  <text
                    fill={tone}
                    fontSize="10"
                    fontWeight="700"
                    textAnchor={index > candles.length - 12 ? "end" : "start"}
                    x={index > candles.length - 12 ? x - 8 : x + 8}
                    y={Math.max(y - 10, 12)}
                  >
                    {index === chart.latestIndex ? "오늘" : index === chart.selectionIndex ? "선정일" : formatShortDate(candle.candle_date)}
                  </text>
                </g>
              );
            })}

          {[candles[0], candles[Math.floor(candles.length / 2)], latest].map((candle, index) => {
            const xSource = index === 0 ? 0 : index === 1 ? Math.floor(candles.length / 2) : chart.latestIndex;
            const x = chart.padLeft + xSource * chart.step;
            return (
              <text
                key={`x-label-${candle.candle_date}`}
                fill="#72807a"
                fontSize="10"
                textAnchor={index === 0 ? "start" : index === 2 ? "end" : "middle"}
                x={x}
                y={chart.height - 8}
              >
                {formatShortDate(candle.candle_date)}
              </text>
            );
          })}
        </svg>
      </div>
    </section>
  );
}

function StockDetailModal({
  target,
  detail,
  loading,
  error,
  onClose,
}: {
  target: { selectionDate: string; item: StockSelectionItem } | null;
  detail: StockDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  if (!target) return null;

  const liveTone =
    (detail?.change_amount ?? 0) > 0 ? "text-accent" : (detail?.change_amount ?? 0) < 0 ? "text-coral" : "text-text";
  const sinceSelectionChange =
    detail?.selection_close_price != null && detail.current_price != null
      ? detail.current_price - detail.selection_close_price
      : null;
  const sinceSelectionRate =
    sinceSelectionChange != null && detail?.selection_close_price
      ? (sinceSelectionChange / detail.selection_close_price) * 100
      : null;
  const sinceSelectionTone =
    (sinceSelectionChange ?? 0) > 0 ? "text-accent" : (sinceSelectionChange ?? 0) < 0 ? "text-coral" : "text-text";

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(23,33,29,0.45)] p-4"
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      role="dialog"
    >
      <div className="surface max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl p-5 md:p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">종목 상세</p>
            <h2 className="mt-2 text-2xl font-bold">
              {target.item.name}
              <span className="ml-2 text-base font-medium text-muted">{target.item.symbol}</span>
            </h2>
            <p className="mt-2 text-sm text-muted">
              선정 요청일 {formatDate(target.selectionDate)}
              {detail?.candle_date && detail.candle_date !== target.selectionDate
                ? ` · 실제 기준 캔들 ${formatDate(detail.candle_date)}`
                : ""}
            </p>
          </div>
          <button
            className="rounded-md border border-line px-3 py-2 text-sm font-semibold text-muted transition hover:border-accent hover:text-accent"
            onClick={onClose}
            type="button"
          >
            닫기
          </button>
        </div>

        <div className="mt-5 grid gap-3 md:grid-cols-4">
          <DetailStat label="선정 점수" value={target.item.score.toFixed(2)} />
          <DetailStat label="선정 당시 평균 거래대금" value={formatQuantity(target.item.avg_trade_amount, "원")} />
          <DetailStat
            label="선정 당시 시가총액"
            value={target.item.market_cap != null ? formatMarketCap(target.item.market_cap) : "-"}
          />
          <DetailStat label="선정 사유" value={target.item.reason} tone="text-muted" />
        </div>

        {loading && <LoadingBar active label={`${target.item.name} 상세 정보를 KIS에서 조회하고 있습니다.`} />}
        {error && (
          <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{error}</p>
        )}

        {!loading && !error && detail && (
          <div className="mt-5 space-y-5">
            <section className="rounded-xl border border-line bg-panel/60 p-4">
              <div className="grid gap-3 md:grid-cols-3">
                <DetailStat label="그 날 종가" value={formatPrice(detail.selection_close_price)} />
                <DetailStat label="오늘 현재가" value={formatPrice(detail.current_price)} tone={liveTone} />
                <DetailStat
                  label="선정일 대비"
                  value={`${formatSignedNumber(sinceSelectionChange)}원 · ${formatSignedPercent(sinceSelectionRate)}`}
                  tone={sinceSelectionTone}
                />
              </div>
            </section>

            <StockDetailChart detail={detail} />

            <section className="rounded-xl border border-line bg-panel/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold">선정일 기준 데이터</h3>
                  <p className="mt-1 text-sm text-muted">해당 일자 일봉 기준으로 선정 당시 가격 흐름을 확인합니다.</p>
                </div>
                <div className="rounded-md bg-white px-3 py-2 text-xs font-semibold text-muted">
                  {detail.market_name ?? "시장 정보 없음"}
                  {detail.sector_name ? ` · ${detail.sector_name}` : ""}
                </div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-5">
                <DetailStat label="종가" value={formatQuantity(detail.selection_close_price, "원")} />
                <DetailStat label="시가" value={formatQuantity(detail.selection_open_price, "원")} />
                <DetailStat label="고가" value={formatQuantity(detail.selection_high_price, "원")} />
                <DetailStat label="저가" value={formatQuantity(detail.selection_low_price, "원")} />
                <DetailStat label="거래량" value={formatQuantity(detail.selection_volume, "주")} />
              </div>
            </section>

            <section className="rounded-xl border border-line bg-panel/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-bold">현재 KIS 시세</h3>
                  <p className="mt-1 text-sm text-muted">현재가 기준의 참고 지표입니다. 선정일 데이터와는 시점이 다를 수 있습니다.</p>
                </div>
                <div className={`rounded-md px-3 py-2 text-sm font-semibold ${liveTone}`}>
                  {formatSignedNumber(detail.change_amount)}원 · {formatSignedPercent(detail.change_rate)}
                </div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-4">
                <DetailStat label="현재가" value={formatQuantity(detail.current_price, "원")} tone={liveTone} />
                <DetailStat label="전일 종가" value={formatQuantity(detail.previous_close, "원")} />
                <DetailStat label="시가총액" value={detail.market_cap != null ? formatMarketCap(detail.market_cap) : "-"} />
                <DetailStat label="상장주식수" value={formatQuantity(detail.shares_outstanding, "주")} />
                <DetailStat label="당일 시가" value={formatQuantity(detail.open_price, "원")} />
                <DetailStat label="당일 고가" value={formatQuantity(detail.high_price, "원")} />
                <DetailStat label="당일 저가" value={formatQuantity(detail.low_price, "원")} />
                <DetailStat label="누적 거래량" value={formatQuantity(detail.volume, "주")} />
                <DetailStat label="누적 거래대금" value={formatQuantity(detail.trade_amount, "원")} />
                <DetailStat label="52주 고가" value={formatQuantity(detail.week52_high, "원")} />
                <DetailStat label="52주 저가" value={formatQuantity(detail.week52_low, "원")} />
                <DetailStat label="PER / PBR" value={`${formatRatio(detail.per)} / ${formatRatio(detail.pbr)}`} />
                <DetailStat label="EPS" value={formatQuantity(detail.eps, "원")} />
                <DetailStat label="BPS" value={formatQuantity(detail.bps, "원")} />
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}

function RangeDateRow({
  row,
  prevSymbols,
  activeSymbol,
  onStockClick,
}: {
  row: StockSelectionDateResult;
  prevSymbols: Set<string>;
  activeSymbol?: string | null;
  onStockClick: (selectionDate: string, item: StockSelectionItem) => void;
}) {
  return (
    <div className="flex flex-wrap items-start gap-3 border-b border-line py-3 last:border-0">
      <span className="w-24 shrink-0 pt-0.5 font-mono text-xs text-muted">{formatDate(row.selection_date)}</span>
      <div className="flex flex-1 flex-wrap gap-1.5">
        {row.selected.length === 0 && (
          <span className="text-xs text-muted">해당 기준 통과 종목 없음</span>
        )}
        {row.selected.map((item) => {
          const isNew = !prevSymbols.has(item.symbol) && prevSymbols.size > 0;
          return (
            <button
              key={item.symbol}
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition ${
                activeSymbol === item.symbol
                  ? "border-accent bg-accentSoft text-accent"
                  : isNew
                  ? "border-accent bg-accentSoft text-accent"
                  : "border-line bg-white text-text hover:border-accent hover:text-accent"
              }`}
              onClick={() => onStockClick(row.selection_date, item)}
              type="button"
            >
              {item.name}
              <span className="font-normal text-muted">{item.symbol}</span>
              {isNew && <span className="ml-0.5 rounded-sm bg-accent px-1 text-[10px] text-white">신규</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function RangeResults({ data }: { data: StockSelectionRangeResult }) {
  const [showAll, setShowAll] = useState(false);
  const [activeDetailTarget, setActiveDetailTarget] = useState<{ selectionDate: string; item: StockSelectionItem } | null>(null);
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Reverse order: newest first
  const rows = useMemo(() => [...data.results].reverse(), [data.results]);
  const visible = showAll ? rows : rows.slice(0, 30);

  // Compute prev symbols for each row (previous day = next in reversed array)
  const prevSetsReversed = useMemo(() => {
    // original order (oldest first): build running set
    const sets: Set<string>[] = [];
    for (let i = 0; i < data.results.length; i++) {
      if (i === 0) {
        sets.push(new Set());
      } else {
        sets.push(new Set(data.results[i - 1].selected.map((s) => s.symbol)));
      }
    }
    return sets.reverse();
  }, [data.results]);

  const changedDays = data.results.filter((row, i) => {
    if (i === 0) return row.selected.length > 0;
    const prev = new Set(data.results[i - 1].selected.map((s) => s.symbol));
    const curr = new Set(row.selected.map((s) => s.symbol));
    return [...prev].some((s) => !curr.has(s)) || [...curr].some((s) => !prev.has(s));
  }).length;

  async function handleStockClick(selectionDate: string, item: StockSelectionItem) {
    setActiveDetailTarget({ selectionDate, item });
    setDetail(null);
    setDetailError(null);
    setDetailLoading(true);
    try {
      const data = await apiFetch<StockDetail>(
        `/backtest/stocks/${item.symbol}/detail?selection_date=${encodeURIComponent(selectionDate)}`
      );
      setDetail(data);
    } catch (exc) {
      setDetailError(exc instanceof Error ? exc.message : "종목 상세 정보를 불러오지 못했습니다.");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <Metric label="분석 영업일" value={`${data.results.length}일`} />
        <Metric label="종목 변동 있는 날" value={`${changedDays}일`} tone="text-accent" />
        <Metric
          label="최근 선정 종목"
          value={`${rows[0]?.selected.length ?? 0}개`}
        />
      </div>

      <NotesList notes={data.notes} />

      <section className="surface rounded-md p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-bold">일자별 선정 종목</h2>
          <span className="text-xs text-muted">최신순 · 클릭 시 상세 팝업 · 초록=신규진입</span>
        </div>
        <div className="divide-y divide-line">
          {visible.map((row, i) => (
            <RangeDateRow
              key={row.selection_date}
              row={row}
              prevSymbols={prevSetsReversed[i]}
              activeSymbol={activeDetailTarget?.selectionDate === row.selection_date ? activeDetailTarget.item.symbol : null}
              onStockClick={handleStockClick}
            />
          ))}
        </div>
        {rows.length > 30 && !showAll && (
          <button
            className="mt-3 w-full rounded-md border border-line py-2 text-sm text-muted hover:border-accent hover:text-accent"
            onClick={() => setShowAll(true)}
            type="button"
          >
            전체 {rows.length}일 보기
          </button>
        )}
      </section>

      {activeDetailTarget && (
        <StockDetailModal
          target={activeDetailTarget}
          detail={detail}
          loading={detailLoading}
          error={detailError}
          onClose={() => {
            setActiveDetailTarget(null);
            setDetail(null);
            setDetailError(null);
            setDetailLoading(false);
          }}
        />
      )}
    </div>
  );
}

export function SelectionTab({
  onGoToStrategy,
}: {
  onGoToStrategy: (stocks: SelectedSymbol[]) => void;
}) {
  const [mode, setMode] = useState<Mode>("single");

  // Single mode state
  const [selDate, setSelDate] = useState(today(-1));
  const [capital, setCapital] = useState("2000000");
  const [maxSymbols, setMaxSymbols] = useState("4");
  const [singleResult, setSingleResult] = useState<StockSelectionResult | null>(null);
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleError, setSingleError] = useState<string | null>(null);

  // Range mode state
  const [rangeStart, setRangeStart] = useState(today(-30));
  const [rangeEnd, setRangeEnd] = useState(today(-1));
  const [rangeCapital, setRangeCapital] = useState("2000000");
  const [rangeMaxSymbols, setRangeMaxSymbols] = useState("4");
  const [rangeResult, setRangeResult] = useState<StockSelectionRangeResult | null>(null);
  const [rangeLoading, setRangeLoading] = useState(false);
  const [rangeError, setRangeError] = useState<string | null>(null);

  async function runSingle() {
    setSingleError(null);
    let parsedCapital: number;
    let parsedMax: number;
    try {
      if (!selDate) throw new Error("기준일을 입력하세요.");
      parsedCapital = parsePositiveNumber(capital, "초기 자본");
      parsedMax = parsePositiveNumber(maxSymbols, "비교 종목 수");
      if (parsedMax > 50) throw new Error("비교 종목 수는 50개 이하로 입력하세요.");
    } catch (exc) {
      setSingleResult(null);
      setSingleError(exc instanceof Error ? exc.message : "입력값을 확인하세요.");
      return;
    }

    setSingleLoading(true);
    try {
      const data = await apiFetch<StockSelectionResult>("/backtest/select", {
        method: "POST",
        body: JSON.stringify({
          selection_date: selDate,
          initial_capital: parsedCapital,
          max_symbols: parsedMax,
        }),
      });
      setSingleResult(data);
    } catch (exc) {
      setSingleResult(null);
      setSingleError(exc instanceof Error ? exc.message : "종목선정에 실패했습니다.");
    } finally {
      setSingleLoading(false);
    }
  }

  async function runRange() {
    setRangeError(null);
    let parsedCapital: number;
    let parsedMax: number;
    try {
      if (!rangeStart || !rangeEnd) throw new Error("시작일과 종료일을 모두 입력하세요.");
      if (rangeStart >= rangeEnd) throw new Error("종료일은 시작일보다 뒤여야 합니다.");
      const span = daysBetween(rangeStart, rangeEnd);
      if (span > 90) throw new Error("최대 90일 범위까지 분석 가능합니다.");
      parsedCapital = parsePositiveNumber(rangeCapital, "초기 자본");
      parsedMax = parsePositiveNumber(rangeMaxSymbols, "비교 종목 수");
      if (parsedMax > 50) throw new Error("비교 종목 수는 50개 이하로 입력하세요.");
    } catch (exc) {
      setRangeResult(null);
      setRangeError(exc instanceof Error ? exc.message : "입력값을 확인하세요.");
      return;
    }

    setRangeLoading(true);
    try {
      const data = await apiFetch<StockSelectionRangeResult>("/backtest/select-range", {
        method: "POST",
        body: JSON.stringify({
          start_date: rangeStart,
          end_date: rangeEnd,
          initial_capital: parsedCapital,
          max_symbols: parsedMax,
        }),
      });
      setRangeResult(data);
    } catch (exc) {
      setRangeResult(null);
      setRangeError(exc instanceof Error ? exc.message : "기간별 종목선정에 실패했습니다.");
    } finally {
      setRangeLoading(false);
    }
  }

  function handleGoToStrategy() {
    if (!singleResult) return;
    const stocks: SelectedSymbol[] = singleResult.selected
      .slice(0, 5)
      .map((item) => ({ symbol: item.symbol, name: item.name }));
    onGoToStrategy(stocks);
  }

  return (
    <div className="space-y-6">
      {/* Mode toggle */}
      <div className="flex gap-1 rounded-md border border-line bg-background p-1 w-fit">
        <button
          className={`rounded px-4 py-1.5 text-sm transition ${mode === "single" ? "bg-white font-semibold text-text shadow-sm" : "text-muted hover:text-text"}`}
          onClick={() => setMode("single")}
          type="button"
        >
          단일 기준일
        </button>
        <button
          className={`rounded px-4 py-1.5 text-sm transition ${mode === "range" ? "bg-white font-semibold text-text shadow-sm" : "text-muted hover:text-text"}`}
          onClick={() => setMode("range")}
          type="button"
        >
          기간 분석
        </button>
      </div>

      {mode === "single" && (
        <>
          <section className="surface rounded-md p-5">
            <div className="grid gap-4 md:grid-cols-3">
              <Input label="기준일" type="date" value={selDate} max={today(-1)} onChange={(e) => setSelDate(e.target.value)} />
              <Input label="초기 자본" type="number" value={capital} onChange={(e) => setCapital(e.target.value)} />
              <Input label="비교 종목 수" type="number" value={maxSymbols} onChange={(e) => setMaxSymbols(e.target.value)} />
            </div>
            <div className="mt-4 flex items-center gap-3">
              <Button onClick={runSingle} disabled={singleLoading}>
                {singleLoading ? "선정 중" : "종목선정 실행"}
              </Button>
            </div>
            {singleLoading && <LoadingBar active label="기준일 기준 종목을 선정하고 있습니다." />}
            {singleError && (
              <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{singleError}</p>
            )}
          </section>

          {singleResult && (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <Metric label="선정 종목" value={`${singleResult.selected.length}개`} />
                <Metric label="기준일" value={selDate} />
                <Metric label="초기 자본" value={`${Number(capital).toLocaleString("ko-KR")}원`} />
              </div>

              <NotesList notes={singleResult.notes} />

              <section className="surface rounded-md p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-bold">선정 종목</h2>
                    <p className="mt-1 text-sm text-muted">시총 우선 + 주가 상한 + 최근 과열 제외</p>
                  </div>
                  {singleResult.selected.length > 0 && (
                    <button
                      className="rounded-md border border-accent bg-accentSoft px-3 py-2 text-sm font-semibold text-accent transition hover:bg-accent hover:text-white"
                      onClick={handleGoToStrategy}
                      type="button"
                    >
                      상위 {Math.min(singleResult.selected.length, 5)}개로 전략 테스트하기 →
                    </button>
                  )}
                </div>
                <StockSelectionGrid selected={singleResult.selected} />
              </section>
            </>
          )}
        </>
      )}

      {mode === "range" && (
        <>
          <section className="surface rounded-md p-5">
            <p className="mb-3 text-sm text-muted">최대 90일 범위 내에서 매 영업일마다 종목선정을 실행합니다.</p>
            <div className="grid gap-4 md:grid-cols-4">
              <Input label="시작일" type="date" value={rangeStart} max={today(-1)} onChange={(e) => setRangeStart(e.target.value)} />
              <Input label="종료일" type="date" value={rangeEnd} max={today(-1)} onChange={(e) => setRangeEnd(e.target.value)} />
              <Input label="초기 자본" type="number" value={rangeCapital} onChange={(e) => setRangeCapital(e.target.value)} />
              <Input label="최대 종목 수" type="number" value={rangeMaxSymbols} onChange={(e) => setRangeMaxSymbols(e.target.value)} />
            </div>
            <div className="mt-4">
              <Button onClick={runRange} disabled={rangeLoading}>
                {rangeLoading ? "분석 중" : "기간 분석 실행"}
              </Button>
            </div>
            {rangeLoading && <LoadingBar active label="기간별 종목선정을 실행하고 있습니다. 잠시 기다려 주세요." />}
            {rangeError && (
              <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{rangeError}</p>
            )}
          </section>

          {rangeResult && <RangeResults data={rangeResult} />}
        </>
      )}
    </div>
  );
}
