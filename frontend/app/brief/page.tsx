"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type { Briefing } from "@/types/api";

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

  const sections = briefing?.content_sections
    ? ["dev", "investment", "ai"]
        .map((key) => briefing.content_sections?.[key])
        .filter((section): section is NonNullable<typeof briefing.content_sections>[string] => Boolean(section))
    : [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">데일리 브리핑</h1>
          <p className="mt-1 text-sm text-muted">오늘의 개발, 투자, AI 이슈</p>
        </div>
        <Link className="rounded-md border border-line px-4 py-3 text-sm" href="/brief/archive">
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
          <section className="rounded-md border border-line bg-panel p-5 shadow-sm shadow-line/40">
            <div className="mb-3 flex flex-wrap gap-2 text-xs text-muted">
              <span>기반 기사 {briefing.source_article_count ?? 0}건</span>
              <span>모델 {briefing.model_used ?? "mock"}</span>
              <span>{new Date(briefing.generated_at).toLocaleString("ko-KR")}</span>
            </div>
            <h2 className="break-words text-2xl font-bold leading-tight">{briefing.one_liner}</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(briefing.keywords ?? []).map((keyword) => (
                <span key={keyword} className="rounded-md bg-accentSoft px-3 py-1 text-sm text-accent">
                  {keyword}
                </span>
              ))}
            </div>
          </section>

          {sections.length > 0 ? (
            <div className="space-y-4">
              {sections.map((section) => (
                <section key={section.label} className="overflow-hidden rounded-md border border-line bg-panel p-5 shadow-sm shadow-line/40">
                  <div className="flex items-center gap-2">
                    <span className="flex h-9 w-9 items-center justify-center rounded-md bg-infoSoft text-info">
                      <Icon name="newspaper" className="h-5 w-5" />
                    </span>
                    <h2 className="text-xl font-bold">{section.label}</h2>
                  </div>
                  <p className="mt-4 line-clamp-3 break-words leading-7 text-muted">{section.summary}</p>
                  <div className="mt-5 space-y-3">
                    {section.highlights.map((highlight) => (
                      <a
                        key={highlight.news_id}
                        href={highlight.url}
                        target="_blank"
                        rel="noreferrer"
                        className="block overflow-hidden rounded-md border border-line p-4 transition hover:border-accent hover:bg-accentSoft/40"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <h3 className="line-clamp-2 break-words font-semibold leading-6">{highlight.title_ko || highlight.title}</h3>
                            {highlight.title_ko && highlight.title_ko !== highlight.title ? (
                              <p className="mt-1 line-clamp-1 break-words text-xs text-muted">원문: {highlight.title}</p>
                            ) : null}
                            <p className="mt-2 line-clamp-3 break-words text-sm leading-6 text-muted">{highlight.reason}</p>
                          </div>
                          <Icon name="arrowRight" className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
                        </div>
                        <p className="mt-2 truncate text-xs text-muted">{highlight.source}</p>
                      </a>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          ) : (
            <Card>
              <div className="prose-brief">
                <ReactMarkdown>{briefing.content_markdown}</ReactMarkdown>
              </div>
            </Card>
          )}
        </>
      ) : !initialLoading ? (
        <Card>
          <p className="text-muted">브리핑을 불러오지 못했습니다.</p>
        </Card>
      ) : null}
    </div>
  );
}
