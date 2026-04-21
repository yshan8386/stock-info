"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { apiFetch, formatDate } from "@/lib/api";
import type { Briefing, GlossaryGroup } from "@/types/api";

export default function HomePage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [totalTerms, setTotalTerms] = useState(0);
  const [recentTerms, setRecentTerms] = useState<string[]>([]);

  useEffect(() => {
    apiFetch<Briefing>("/brief/today")
      .then(setBriefing)
      .catch(() => setBriefing(null));
    apiFetch<GlossaryGroup[]>("/glossary")
      .then((groups) => {
        setTotalTerms(groups.reduce((sum, group) => sum + group.terms.length, 0));
        setRecentTerms(groups.flatMap((group) => group.terms.slice(0, 2).map((term) => term.term_ko)).slice(0, 4));
      })
      .catch(() => {
        setTotalTerms(0);
        setRecentTerms([]);
      });
  }, []);

  return (
    <div className="space-y-7">
      <section className="surface overflow-hidden rounded-md p-6 md:p-8">
        <div className="grid gap-6 md:grid-cols-[1.4fr_0.8fr] md:items-end">
          <div>
            <p className="text-sm font-semibold text-accent">{formatDate(new Date().toISOString())}</p>
            <h1 className="mt-4 max-w-3xl text-3xl font-bold leading-tight md:text-5xl">
              시장 뉴스와 투자 개념을 한 화면에서 정리합니다.
            </h1>
            <p className="mt-4 max-w-2xl leading-7 text-muted">
              데일리 브리핑과 투자 개념 정리는 로그인 없이 볼 수 있습니다. 백테스트와 투자 현황은 계정 생성 후 이용할 수 있습니다.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link className="rounded-md bg-text px-4 py-3 text-sm font-semibold text-white transition hover:bg-accent" href="/brief">
                오늘 브리핑 보기
              </Link>
              <Link className="rounded-md border border-line bg-white px-4 py-3 text-sm font-semibold text-text transition hover:border-accent hover:bg-accentSoft" href="/glossary">
                투자 개념 검색
              </Link>
            </div>
          </div>
          <div className="grid gap-3 rounded-md border border-line bg-white/70 p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted">공개 콘텐츠</span>
              <span className="rounded-md bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">로그인 불필요</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-md border border-line bg-white p-4">
                <p className="text-sm text-muted">브리핑 기준 기사</p>
                <p className="mt-2 text-2xl font-bold">{briefing?.source_article_count ?? 0}</p>
              </div>
              <div className="rounded-md border border-line bg-white p-4">
                <p className="text-sm text-muted">투자 개념</p>
                <p className="mt-2 text-2xl font-bold">{totalTerms}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <Link href="/brief">
          <Card className="h-full transition hover:-translate-y-0.5 hover:border-accent">
            <div className="mb-4 flex items-center justify-between">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-accentSoft text-accent">
                <Icon name="newspaper" className="h-5 w-5" />
              </span>
              <Icon name="arrowRight" className="h-5 w-5 text-muted" />
            </div>
            <h2 className="text-xl font-bold">데일리 브리핑</h2>
            <p className="text-sm text-muted">
              {briefing ? `${briefing.briefing_date} 생성` : "최근 브리핑을 준비합니다"}
            </p>
            <p className="mt-4 line-clamp-3 text-lg leading-7">{briefing?.one_liner ?? "수집된 기사로 핵심 이슈를 정리합니다."}</p>
          </Card>
        </Link>

        <Link href="/glossary">
          <Card className="h-full transition hover:-translate-y-0.5 hover:border-info">
            <div className="mb-4 flex items-center justify-between">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-infoSoft text-info">
                <Icon name="book" className="h-5 w-5" />
              </span>
              <Icon name="arrowRight" className="h-5 w-5 text-muted" />
            </div>
            <h2 className="text-xl font-bold">투자 개념 정리</h2>
            <p className="text-sm text-muted">등록된 개념 {totalTerms}개</p>
            <p className="mt-4 text-lg">
              주요 개념: {recentTerms.join(", ") || "시드 데이터 준비 중"}
            </p>
          </Card>
        </Link>

        <Link href="/backtest">
          <Card className="h-full border-dashed">
            <span className="rounded-md bg-warnSoft px-2.5 py-1 text-xs font-semibold text-warn">로그인 후 이용</span>
            <h2 className="text-xl font-bold">백테스트</h2>
            <p className="mt-4 text-muted">투자 전략을 과거 데이터로 검증하는 기능을 준비하고 있습니다.</p>
          </Card>
        </Link>

        <Link href="/position">
          <Card className="h-full border-dashed">
            <span className="rounded-md bg-coralSoft px-2.5 py-1 text-xs font-semibold text-coral">로그인 후 이용</span>
            <h2 className="text-xl font-bold">투자 현황</h2>
            <p className="mt-4 text-muted">포트폴리오 조회와 손익 추적 기능을 준비하고 있습니다.</p>
          </Card>
        </Link>
      </div>
    </div>
  );
}
