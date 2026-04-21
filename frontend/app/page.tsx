"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { apiFetch, formatDate } from "@/lib/api";
import type { DashboardSummary } from "@/types/api";

export default function HomePage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  useEffect(() => {
    apiFetch<DashboardSummary>("/dashboard/summary").then(setSummary).catch(() => setSummary(null));
  }, []);

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-bold">안녕하세요.</h1>
        <p className="mt-2 text-muted">{formatDate(new Date().toISOString())}</p>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/brief">
          <Card className="h-full transition hover:border-accent hover:bg-accentSoft/50">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">데일리 브리핑</h2>
              <Icon name="arrowRight" className="h-5 w-5 text-accent" />
            </div>
            <p className="text-sm text-muted">
              {summary?.today_briefing
                ? `${summary.today_briefing.briefing_date} 생성`
                : "오늘의 브리핑을 준비합니다"}
            </p>
            <p className="mt-4 text-lg">{summary?.today_briefing?.one_liner ?? "수집된 기사로 핵심 이슈를 정리합니다."}</p>
          </Card>
        </Link>

        <Link href="/glossary">
          <Card className="h-full transition hover:border-accent hover:bg-infoSoft/60">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">투자 개념 정리</h2>
              <Icon name="arrowRight" className="h-5 w-5 text-info" />
            </div>
            <p className="text-sm text-muted">등록된 개념 {summary?.glossary.total_terms ?? 0}개</p>
            <p className="mt-4 text-lg">
              최근 추가: {summary?.glossary.recent_added.join(", ") || "시드 데이터 준비 중"}
            </p>
          </Card>
        </Link>

        <Link href="/backtest">
          <Card className="h-full">
            <h2 className="text-xl font-bold">백테스트</h2>
            <p className="mt-4 text-muted">투자 전략을 과거 데이터로 검증하는 기능을 준비하고 있습니다.</p>
          </Card>
        </Link>

        <Link href="/position">
          <Card className="h-full">
            <h2 className="text-xl font-bold">투자 현황</h2>
            <p className="mt-4 text-muted">포트폴리오 조회와 손익 추적 기능을 준비하고 있습니다.</p>
          </Card>
        </Link>
      </div>
    </div>
  );
}
