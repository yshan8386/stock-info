"use client";

import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api";
import type { PositionDashboard, StrategyInfo } from "@/types/api";

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

const DEFAULT_DASHBOARD: PositionDashboard = {
  mode: "read_only",
  trading_enabled: false,
  as_of: new Date().toISOString(),
  settings: {
    batch_enabled: false,
    live_trading_enabled: false,
    selected_strategy_ids: DEFAULT_STRATEGIES.map((strategy) => strategy.id),
    batch_interval_seconds: 10,
  },
  batch: {
    is_running: false,
    last_run_at: null,
    last_run_status: null,
    captured_signal_count: 0,
    message: "배치가 꺼져 있습니다.",
  },
  account: {
    total_equity: 0,
    cash: 0,
    invested_amount: 0,
    day_pnl: 0,
    day_pnl_pct: 0,
    total_pnl: 0,
    total_pnl_pct: 0,
    buying_power: 0,
  },
  risk_statuses: [
    { name: "자동 주문", status: "blocked", message: "읽기 전용 모드입니다." },
    { name: "계좌 연결", status: "watch", message: "실전 계좌 연결 전입니다." },
  ],
  strategies: [],
  positions: [],
  watchlist: [],
  recent_signals: [],
};

const currencyFormatter = new Intl.NumberFormat("ko-KR", {
  maximumFractionDigits: 0,
});

function won(value: number): string {
  return `${currencyFormatter.format(value)}원`;
}

function signedWon(value: number): string {
  return `${value >= 0 ? "+" : "-"}${won(Math.abs(value))}`;
}

function signedPct(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function pnlColor(value: number): string {
  if (value > 0) return "text-accent";
  if (value < 0) return "text-coral";
  return "text-muted";
}

function riskTone(status: PositionDashboard["risk_statuses"][number]["status"]): string {
  if (status === "ok") return "border-accentSoft bg-accentSoft text-accent";
  if (status === "watch") return "border-warnSoft bg-warnSoft text-warn";
  return "border-coralSoft bg-coralSoft text-coral";
}

function strategyStatusLabel(status: PositionDashboard["strategies"][number]["status"]): string {
  if (status === "active") return "운용 중";
  if (status === "watching") return "관찰 중";
  return "일시 중지";
}

function signalStatusLabel(status: string): string {
  if (status === "ready_for_live_order") return "실투자 요청";
  if (status === "captured") return "시그널 저장";
  return status;
}

export default function PositionPage() {
  const [strategies, setStrategies] = useState<StrategyInfo[]>(DEFAULT_STRATEGIES);
  const [dashboard, setDashboard] = useState<PositionDashboard>(DEFAULT_DASHBOARD);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [savingSettings, setSavingSettings] = useState(false);

  useEffect(() => {
    apiFetch<StrategyInfo[]>("/backtest/strategies")
      .then((data) => {
        if (data.length) setStrategies(data);
      })
      .catch(() => setStrategies(DEFAULT_STRATEGIES));
    apiFetch<PositionDashboard>("/position/dashboard")
      .then((data) => {
        setDashboard(data);
        setDashboardError(null);
      })
      .catch(() => {
        setDashboard(DEFAULT_DASHBOARD);
        setDashboardError("실전투자 대시보드 데이터를 불러오지 못했습니다.");
      });
  }, []);

  useEffect(() => {
    if (!dashboard.settings.batch_enabled) return;
    const intervalMs = Math.max(dashboard.settings.batch_interval_seconds, 5) * 1000;
    const timer = window.setInterval(async () => {
      try {
        await apiFetch("/position/batch/run", { method: "POST" });
        const data = await apiFetch<PositionDashboard>("/position/dashboard");
        setDashboard(data);
        setDashboardError(null);
      } catch {
        setDashboardError("배치 실행 상태를 갱신하지 못했습니다.");
      }
    }, intervalMs);
    return () => window.clearInterval(timer);
  }, [dashboard.settings.batch_enabled, dashboard.settings.batch_interval_seconds]);

  async function refreshDashboard() {
    const data = await apiFetch<PositionDashboard>("/position/dashboard");
    setDashboard(data);
    setDashboardError(null);
  }

  async function updateSettings(next: Partial<PositionDashboard["settings"]>) {
    setSavingSettings(true);
    try {
      await apiFetch("/position/settings", {
        method: "PATCH",
        body: JSON.stringify(next),
      });
      await refreshDashboard();
    } catch (exc) {
      setDashboardError(exc instanceof Error ? exc.message : "운용 설정 저장에 실패했습니다.");
    } finally {
      setSavingSettings(false);
    }
  }

  async function runBatchNow() {
    try {
      await apiFetch("/position/batch/run", { method: "POST" });
      await refreshDashboard();
    } catch (exc) {
      setDashboardError(exc instanceof Error ? exc.message : "배치 실행에 실패했습니다.");
    }
  }

  function toggleStrategy(strategyId: string) {
    const current = dashboard.settings.selected_strategy_ids;
    const next = current.includes(strategyId)
      ? current.filter((item) => item !== strategyId)
      : [...current, strategyId];
    updateSettings({ selected_strategy_ids: next });
  }

  const strategyNames = new Map(strategies.map((strategy) => [strategy.id, strategy.label]));
  const investedRatio =
    dashboard.account.total_equity > 0
      ? Math.round((dashboard.account.invested_amount / dashboard.account.total_equity) * 100)
      : 0;

  return (
    <div className="font-backtest space-y-6">
      <section className="surface overflow-hidden rounded-md p-5 md:p-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-infoSoft text-info">
                <Icon name="briefcase" className="h-5 w-5" />
              </span>
              <span className="rounded-md bg-coralSoft px-2.5 py-1 text-xs font-semibold text-coral">
                자동 주문 비활성
              </span>
              <span className="rounded-md bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">
                {dashboard.mode === "read_only" ? "읽기 전용" : dashboard.mode}
              </span>
            </div>
            <h1 className="mt-4 text-3xl font-bold">실전투자 대시보드</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              백테스트 전략을 실제 운용 화면으로 이어가기 위한 관제판입니다. 현재는 포지션과 리스크 상태를 확인하는 단계이며, 주문 실행은 명시적으로 막아 둡니다.
            </p>
          </div>
          <div className="rounded-md border border-line bg-white px-4 py-3 text-sm">
            <p className="text-muted">마지막 갱신</p>
            <p className="mt-1 font-semibold">{new Date(dashboard.as_of).toLocaleString("ko-KR")}</p>
          </div>
        </div>
        {dashboardError && (
          <p className="mt-4 rounded-md bg-coralSoft px-4 py-3 text-sm font-semibold text-coral">{dashboardError}</p>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <Card>
          <p className="text-sm text-muted">총 평가자산</p>
          <p className="mt-2 text-2xl font-bold">{won(dashboard.account.total_equity)}</p>
          <p className={`mt-2 text-sm font-semibold ${pnlColor(dashboard.account.total_pnl)}`}>
            {signedWon(dashboard.account.total_pnl)} {signedPct(dashboard.account.total_pnl_pct)}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">금일 손익</p>
          <p className={`mt-2 text-2xl font-bold ${pnlColor(dashboard.account.day_pnl)}`}>
            {signedWon(dashboard.account.day_pnl)}
          </p>
          <p className={`mt-2 text-sm font-semibold ${pnlColor(dashboard.account.day_pnl_pct)}`}>
            {signedPct(dashboard.account.day_pnl_pct)}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-muted">투입 비중</p>
          <p className="mt-2 text-2xl font-bold">{investedRatio}%</p>
          <p className="mt-2 text-sm text-muted">{won(dashboard.account.invested_amount)} 운용 중</p>
        </Card>
        <Card>
          <p className="text-sm text-muted">주문 가능 현금</p>
          <p className="mt-2 text-2xl font-bold">{won(dashboard.account.buying_power)}</p>
          <p className="mt-2 text-sm text-muted">현금 {won(dashboard.account.cash)}</p>
        </Card>
      </section>

      <section className="surface rounded-md p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold">운용 설정</h2>
            <p className="mt-1 text-sm text-muted">
              배치 실행이 켜져 있으면 주기적으로 시그널을 탐색합니다. 실투자가 꺼져 있으면 주문 없이 DB에 시그널만 저장합니다.
            </p>
          </div>
          <button
            className="rounded-md border border-line bg-white px-4 py-2 text-sm font-semibold text-text transition hover:border-accent disabled:opacity-60"
            disabled={savingSettings || !dashboard.settings.batch_enabled}
            onClick={runBatchNow}
            type="button"
          >
            지금 실행
          </button>
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="grid gap-3 sm:grid-cols-2">
            <button
              className={`rounded-md border px-4 py-4 text-left transition ${
                dashboard.settings.batch_enabled ? "border-accent bg-accentSoft text-accent" : "border-line bg-white text-muted"
              }`}
              disabled={savingSettings}
              onClick={() => updateSettings({ batch_enabled: !dashboard.settings.batch_enabled })}
              type="button"
            >
              <span className="text-xs font-semibold">배치 실행</span>
              <span className="mt-2 block text-2xl font-bold">{dashboard.settings.batch_enabled ? "ON" : "OFF"}</span>
              <span className="mt-2 block text-sm">주기 {dashboard.settings.batch_interval_seconds}초</span>
            </button>
            <button
              className={`rounded-md border px-4 py-4 text-left transition ${
                dashboard.settings.live_trading_enabled ? "border-coral bg-coralSoft text-coral" : "border-line bg-white text-muted"
              }`}
              disabled={savingSettings}
              onClick={() => updateSettings({ live_trading_enabled: !dashboard.settings.live_trading_enabled })}
              type="button"
            >
              <span className="text-xs font-semibold">실투자</span>
              <span className="mt-2 block text-2xl font-bold">{dashboard.settings.live_trading_enabled ? "ON" : "OFF"}</span>
              <span className="mt-2 block text-sm">
                {dashboard.settings.live_trading_enabled ? "실투자 요청 모드" : "시그널 저장 모드"}
              </span>
            </button>
          </div>
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="font-semibold">전략 선택</p>
              <span className="text-xs text-muted">{dashboard.settings.selected_strategy_ids.length}개 선택</span>
            </div>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {strategies.map((strategy) => {
                const selected = dashboard.settings.selected_strategy_ids.includes(strategy.id);
                return (
                  <button
                    key={strategy.id}
                    className={`rounded-md border px-4 py-3 text-left transition ${
                      selected ? "border-info bg-infoSoft text-info" : "border-line bg-white text-muted hover:text-text"
                    }`}
                    disabled={savingSettings}
                    onClick={() => toggleStrategy(strategy.id)}
                    type="button"
                  >
                    <span className="font-semibold">{strategy.label}</span>
                    <span className="mt-1 block text-xs leading-5">{strategy.description}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        <p className="mt-4 rounded-md bg-background px-4 py-3 text-sm text-muted">
          {dashboard.batch.message} 최근 실행:{" "}
          {dashboard.batch.last_run_at ? new Date(dashboard.batch.last_run_at).toLocaleTimeString("ko-KR") : "없음"} · 최근 포착{" "}
          {dashboard.batch.captured_signal_count}개
        </p>
      </section>

      <section className="surface rounded-md p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">리스크 게이트</h2>
            <p className="mt-1 text-sm text-muted">실전 전환 전에 반드시 열려 있어야 하는 상태값입니다.</p>
          </div>
          <span className="rounded-md bg-coralSoft px-2.5 py-1 text-xs font-semibold text-coral">
            주문 실행 차단
          </span>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          {dashboard.risk_statuses.map((item) => (
            <div key={item.name} className={`rounded-md border px-4 py-3 ${riskTone(item.status)}`}>
              <p className="font-semibold">{item.name}</p>
              <p className="mt-2 text-sm leading-5">{item.message}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="surface rounded-md p-5">
          <h2 className="text-xl font-bold">전략별 운용 상태</h2>
          <p className="mt-1 text-sm text-muted">백테스트 전략을 그대로 실전 운용 단위로 봅니다.</p>
          <div className="mt-4 grid gap-3">
            {dashboard.strategies.map((strategy) => {
              const deployedPct =
                strategy.allocated_capital > 0
                  ? Math.round((strategy.deployed_capital / strategy.allocated_capital) * 100)
                  : 0;
              return (
                <div key={strategy.strategy_id} className="rounded-md border border-line bg-white p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-semibold">{strategy.strategy_label}</p>
                      <p className="mt-1 text-xs text-muted">{strategy.strategy_id}</p>
                    </div>
                    <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
                      {strategyStatusLabel(strategy.status)}
                    </span>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-3">
                    <div>
                      <p className="text-xs text-muted">투입</p>
                      <p className="font-semibold">{won(strategy.deployed_capital)}</p>
                      <p className="text-xs text-muted">배정 대비 {deployedPct}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted">보유</p>
                      <p className="font-semibold">
                        {strategy.open_positions}/{strategy.max_positions}개
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted">평가손익</p>
                      <p className={`font-semibold ${pnlColor(strategy.unrealized_pnl)}`}>
                        {signedWon(strategy.unrealized_pnl)} {signedPct(strategy.unrealized_pnl_pct)}
                      </p>
                    </div>
                  </div>
                  <p className="mt-4 rounded-md bg-background px-3 py-2 text-sm text-muted">{strategy.next_action}</p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="surface rounded-md p-5">
          <h2 className="text-xl font-bold">관심 신호</h2>
          <p className="mt-1 text-sm text-muted">진입 전 확인해야 할 트리거입니다.</p>
          <div className="mt-4 grid gap-3">
            {dashboard.watchlist.map((item) => (
              <div key={item.symbol} className="rounded-md border border-line bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">
                      {item.name} <span className="text-xs text-muted">{item.symbol}</span>
                    </p>
                    <p className="mt-1 text-sm text-muted">{strategyNames.get(item.strategy_id) ?? item.strategy_id}</p>
                  </div>
                  <span className="rounded-md bg-warnSoft px-2.5 py-1 text-xs font-semibold text-warn">대기</span>
                </div>
                <p className="mt-3 text-sm font-semibold">{item.signal}</p>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <p>
                    <span className="block text-xs text-muted">현재가</span>
                    {won(item.current_price)}
                  </p>
                  <p>
                    <span className="block text-xs text-muted">트리거</span>
                    {won(item.trigger_price)}
                  </p>
                </div>
                <p className="mt-3 rounded-md bg-background px-3 py-2 text-xs text-muted">{item.risk_note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="surface rounded-md p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">배치 포착 시그널</h2>
            <p className="mt-1 text-sm text-muted">실투자 OFF에서는 이 목록만 DB에 저장되고 주문은 나가지 않습니다.</p>
          </div>
          <span className="rounded-md bg-infoSoft px-2.5 py-1 text-xs font-semibold text-info">
            {dashboard.recent_signals.length}개 표시
          </span>
        </div>
        <div className="mt-4 grid gap-3">
          {dashboard.recent_signals.length === 0 ? (
            <p className="rounded-md border border-dashed border-line bg-white px-4 py-6 text-center text-sm text-muted">
              아직 저장된 시그널이 없습니다. 배치 실행을 켠 뒤 기다리거나 지금 실행을 눌러주세요.
            </p>
          ) : (
            dashboard.recent_signals.map((signal) => (
              <div key={signal.id} className="rounded-md border border-line bg-white p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">
                      {signal.name} <span className="text-xs text-muted">{signal.symbol}</span>
                    </p>
                    <p className="mt-1 text-sm text-muted">{strategyNames.get(signal.strategy_id) ?? signal.strategy_id}</p>
                  </div>
                  <span className={`rounded-md px-2.5 py-1 text-xs font-semibold ${
                    signal.status === "ready_for_live_order" ? "bg-coralSoft text-coral" : "bg-accentSoft text-accent"
                  }`}>
                    {signalStatusLabel(signal.status)}
                  </span>
                </div>
                <p className="mt-3 text-sm font-semibold">{signal.signal}</p>
                <div className="mt-3 grid gap-3 text-sm sm:grid-cols-4">
                  <p>
                    <span className="block text-xs text-muted">현재가</span>
                    {won(signal.current_price)}
                  </p>
                  <p>
                    <span className="block text-xs text-muted">트리거</span>
                    {won(signal.trigger_price)}
                  </p>
                  <p>
                    <span className="block text-xs text-muted">신뢰도</span>
                    {Math.round(signal.confidence * 100)}%
                  </p>
                  <p>
                    <span className="block text-xs text-muted">포착 시각</span>
                    {new Date(signal.created_at).toLocaleTimeString("ko-KR")}
                  </p>
                </div>
                <p className="mt-3 rounded-md bg-background px-3 py-2 text-xs text-muted">{signal.risk_note}</p>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="surface rounded-md p-5">
        <h2 className="text-xl font-bold">보유 포지션</h2>
        <p className="mt-1 text-sm text-muted">전략, 손절가, 목표가를 함께 확인합니다.</p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[860px] border-separate border-spacing-0 text-sm">
            <thead>
              <tr className="text-left text-xs text-muted">
                <th className="border-b border-line px-3 py-2">종목</th>
                <th className="border-b border-line px-3 py-2">전략</th>
                <th className="border-b border-line px-3 py-2 text-right">수량</th>
                <th className="border-b border-line px-3 py-2 text-right">평균/현재</th>
                <th className="border-b border-line px-3 py-2 text-right">평가금액</th>
                <th className="border-b border-line px-3 py-2 text-right">손익</th>
                <th className="border-b border-line px-3 py-2 text-right">손절/목표</th>
                <th className="border-b border-line px-3 py-2">진입 근거</th>
              </tr>
            </thead>
            <tbody>
              {dashboard.positions.map((position) => (
                <tr key={`${position.strategy_id}-${position.symbol}`}>
                  <td className="border-b border-line px-3 py-3">
                    <p className="font-semibold">{position.name}</p>
                    <p className="text-xs text-muted">{position.symbol}</p>
                  </td>
                  <td className="border-b border-line px-3 py-3">{strategyNames.get(position.strategy_id) ?? position.strategy_id}</td>
                  <td className="border-b border-line px-3 py-3 text-right">{position.quantity}</td>
                  <td className="border-b border-line px-3 py-3 text-right">
                    <p>{won(position.average_price)}</p>
                    <p className="text-xs text-muted">{won(position.current_price)}</p>
                  </td>
                  <td className="border-b border-line px-3 py-3 text-right font-semibold">{won(position.market_value)}</td>
                  <td className={`border-b border-line px-3 py-3 text-right font-semibold ${pnlColor(position.unrealized_pnl)}`}>
                    <p>{signedWon(position.unrealized_pnl)}</p>
                    <p className="text-xs">{signedPct(position.unrealized_pnl_pct)}</p>
                  </td>
                  <td className="border-b border-line px-3 py-3 text-right">
                    <p className="text-coral">{won(position.stop_loss)}</p>
                    <p className="text-xs text-accent">{won(position.take_profit)}</p>
                  </td>
                  <td className="border-b border-line px-3 py-3 text-muted">{position.entry_reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="surface rounded-md p-5">
        <h2 className="text-xl font-bold">등록 전략 설명</h2>
        <p className="mt-1 text-sm text-muted">실전 운용 화면은 아래 백테스트 전략 정의와 같은 ID를 사용합니다.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {strategies.map((strategy) => (
            <div key={strategy.id} className="rounded-md border border-line bg-white p-4">
              <p className="font-semibold">{strategy.label}</p>
              <p className="mt-2 text-sm leading-6 text-muted">{strategy.description}</p>
              <p className="mt-3 text-xs text-muted">전략 ID: {strategy.id}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
