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
    <div className="space-y-8">
      <section className="surface overflow-hidden rounded-md p-6 md:p-8">
        <div className="grid gap-6 md:grid-cols-[1.4fr_0.8fr] md:items-end">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-sm font-semibold text-accent">{formatDate(new Date().toISOString())}</p>
              <span className="rounded-md bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">공개 콘텐츠 먼저</span>
            </div>
            <h1 className="mt-4 max-w-3xl text-3xl font-bold leading-tight md:text-5xl">
              오늘 읽을 뉴스와 헷갈리는 투자 개념을 빠르게 정리하세요.
            </h1>
            <p className="mt-4 max-w-2xl leading-7 text-muted">
              첫 화면에서 바로 브리핑을 확인하고, 모르는 용어는 개념 정리에서 찾아볼 수 있습니다. 계정이 필요한 기능은 명확히 분리했습니다.
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
              <span className="text-sm font-semibold text-text">오늘 상태</span>
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
            <p className="rounded-md bg-warnSoft px-3 py-2 text-sm leading-6 text-warn">
              백테스트와 실전투자는 개인 데이터가 필요해서 로그인 후 열립니다.
            </p>
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-accent">바로 보기</p>
            <h2 className="text-2xl font-bold">로그인 없이 시작</h2>
          </div>
          <p className="hidden text-sm text-muted md:block">뉴스 확인 → 개념 검색 순서로 보는 흐름입니다.</p>
        </div>
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
        </div>
      </section>

      <section className="space-y-3">
        <div>
          <p className="text-sm font-semibold text-muted">개인 기능</p>
          <h2 className="text-2xl font-bold">로그인 후 이용</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
        <Link href="/backtest">
          <Card className="h-full border-dashed">
            <span className="rounded-md bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">이용 가능</span>
            <h2 className="text-xl font-bold">백테스트</h2>
            <p className="mt-4 text-muted">시총 우선 종목군에 눌림목 반등, 지지·저항 돌파 전략을 동시에 실행해 비교합니다.</p>
          </Card>
        </Link>

        <Link href="/position">
          <Card className="h-full border-dashed">
            <span className="rounded-md bg-coralSoft px-2.5 py-1 text-xs font-semibold text-coral">계정 필요</span>
            <h2 className="text-xl font-bold">실전투자</h2>
            <p className="mt-4 text-muted">배치 실행, 실투자 여부, 전략 선택과 계좌 손익 상태를 한 화면에서 확인합니다.</p>
          </Card>
        </Link>
        </div>
      </section>
    </div>
  );
}
