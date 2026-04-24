"use client";

import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api";
import type { StrategyInfo } from "@/types/api";

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

export default function PositionPage() {
  const [strategies, setStrategies] = useState<StrategyInfo[]>(DEFAULT_STRATEGIES);

  useEffect(() => {
    apiFetch<StrategyInfo[]>("/backtest/strategies")
      .then((data) => {
        if (data.length) setStrategies(data);
      })
      .catch(() => setStrategies(DEFAULT_STRATEGIES));
  }, []);

  return (
    <div className="space-y-6">
      <Card className="mx-auto max-w-4xl">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-md bg-infoSoft text-info">
            <Icon name="briefcase" className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">실전투자</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              실전투자 화면에는 백테스트에서 비교한 전략을 그대로 연결할 예정입니다. 종목선정 기준과 전략 설명을 먼저 고정해 두고, 이후 실시간 시세와 포지션 관리 기능을 얹는 구조로 갑니다.
            </p>
          </div>
        </div>
      </Card>

      <section className="surface rounded-md p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">적용 예정 전략</h2>
            <p className="mt-1 text-sm text-muted">실전 계좌 연결 시 이 전략 설명과 상태가 그대로 노출됩니다.</p>
          </div>
          <span className="rounded-md bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">
            현재 등록 {strategies.length}개
          </span>
        </div>
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

      <section className="surface rounded-md p-5">
        <h2 className="text-xl font-bold">다음 단계</h2>
        <div className="mt-4 grid gap-3 text-sm text-muted">
          <p>공통 종목군과 전략 정의를 백테스트와 동일하게 유지</p>
          <p>전략별 현재 진입 가능 종목과 보유 종목 상태를 분리 표시</p>
          <p>실시간 시세, 주문 가능 수량, 손절/익절 상태를 전략 단위로 추적</p>
        </div>
      </section>
    </div>
  );
}
