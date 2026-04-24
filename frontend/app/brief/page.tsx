"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { BriefingSections } from "@/components/brief/BriefingSections";
import { Card } from "@/components/ui/Card";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type { Briefing } from "@/types/api";

const briefingTypeLabels: Record<string, string> = {
  daily_morning: "아침 브리핑",
  daily_afternoon: "오후 브리핑"
};

export default function BriefPage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);

  async function load() {
    const data = await apiFetch<Briefing>("/brief/today");
    setBriefing(data);
  }

  useEffect(() => {
    load()
      .catch(() => setBriefing(null))
      .finally(() => setInitialLoading(false));
  }, []);

  return (
    <div className="font-briefing space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-accent">로그인 없이 볼 수 있습니다</p>
          <h1 className="mt-1 text-3xl font-bold">데일리 브리핑</h1>
          <p className="mt-2 text-sm text-muted">개발, 투자, AI 이슈를 읽기 쉬운 단위로 정리합니다.</p>
        </div>
        <Link className="rounded-md border border-line bg-white px-4 py-3 text-sm font-semibold transition hover:border-accent hover:bg-accentSoft" href="/brief/archive">
          아카이브
        </Link>
      </div>

      {initialLoading ? (
        <Card>
          <LoadingBar active label="오늘 브리핑을 불러오는 중입니다." />
        </Card>
      ) : null}

      {!initialLoading && briefing ? (
        <>
          <section className="surface rounded-md p-6 md:p-7">
            <div className="mb-4 flex flex-wrap gap-2 text-xs font-semibold">
              <span className="rounded-md bg-white px-2.5 py-1 text-foreground">
                {briefingTypeLabels[briefing.briefing_type] ?? "데일리 브리핑"}
              </span>
              <span className="rounded-md bg-accentSoft px-2.5 py-1 text-accent">기반 기사 {briefing.source_article_count ?? 0}건</span>
              <span className="rounded-md bg-infoSoft px-2.5 py-1 text-info">{new Date(briefing.generated_at).toLocaleString("ko-KR")}</span>
            </div>
            <h2 className="max-w-4xl break-words text-2xl font-bold leading-tight md:text-4xl">{briefing.one_liner}</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(briefing.keywords ?? []).map((keyword) => (
                <span key={keyword} className="rounded-md bg-accentSoft px-3 py-1 text-sm text-accent">
                  {keyword}
                </span>
              ))}
            </div>
          </section>

          {briefing.content_sections ? (
            <BriefingSections briefing={briefing} />
          ) : (
            <Card>
              <div className="prose-brief">
                <ReactMarkdown>{briefing.content_markdown}</ReactMarkdown>
              </div>
            </Card>
          )}
        </>
      ) : !initialLoading ? (
        <Card className="text-center">
          <p className="font-semibold">아직 볼 수 있는 브리핑이 없습니다.</p>
          <p className="mt-2 text-sm text-muted">브리핑이 생성되면 이 화면에 자동으로 표시됩니다.</p>
        </Card>
      ) : null}
    </div>
  );
}
