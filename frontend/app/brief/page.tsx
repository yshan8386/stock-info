"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";
import type { Briefing } from "@/types/api";

const sectionStyles = [
  { tone: "bg-infoSoft text-info", label: "기술 변화" },
  { tone: "bg-accentSoft text-accent", label: "투자 판단" },
  { tone: "bg-warnSoft text-warn", label: "AI 동향" }
];

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
    <div className="space-y-6">
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

          {sections.length > 0 ? (
            <div className="grid gap-4">
              {sections.map((section, index) => {
                const style = sectionStyles[index] ?? sectionStyles[0];
                return (
                  <section key={section.label} className="surface overflow-hidden rounded-md p-5 md:p-6">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <span className={`flex h-10 w-10 items-center justify-center rounded-md ${style.tone}`}>
                          <Icon name="newspaper" className="h-5 w-5" />
                        </span>
                        <div>
                          <p className="text-xs font-semibold text-muted">{style.label}</p>
                          <h2 className="text-xl font-bold">{section.label}</h2>
                        </div>
                      </div>
                      <span className="rounded-md border border-line bg-white px-2.5 py-1 text-xs text-muted">
                        주요 기사 {section.highlights.length}건
                      </span>
                    </div>
                    <p className="mt-4 break-words rounded-md bg-white/70 p-4 leading-7 text-muted">{section.summary}</p>
                    <div className="mt-4 grid gap-3">
                      {section.highlights.map((highlight, highlightIndex) => (
                        <a
                          key={highlight.news_id}
                          href={highlight.url}
                          target="_blank"
                          rel="noreferrer"
                          className="block overflow-hidden rounded-md border border-line bg-white p-4 transition hover:border-accent hover:bg-accentSoft/40"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-background text-xs font-bold text-muted">
                              {highlightIndex + 1}
                            </span>
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
                );
              })}
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
        <Card className="text-center">
          <p className="font-semibold">아직 볼 수 있는 브리핑이 없습니다.</p>
          <p className="mt-2 text-sm text-muted">브리핑이 생성되면 이 화면에 자동으로 표시됩니다.</p>
        </Card>
      ) : null}
    </div>
  );
}
