"use client";

import { Icon } from "@/components/ui/Icon";
import type { Briefing } from "@/types/api";

const sectionStyles = [
  { tone: "bg-infoSoft text-info", label: "기술 변화" },
  { tone: "bg-accentSoft text-accent", label: "투자 판단" },
  { tone: "bg-warnSoft text-warn", label: "AI 동향" }
];

type BriefingSectionsProps = {
  briefing: Briefing;
};

export function BriefingSections({ briefing }: BriefingSectionsProps) {
  const sections = briefing.content_sections
    ? ["dev", "investment", "ai"]
        .map((key) => briefing.content_sections?.[key])
        .filter((section): section is NonNullable<typeof briefing.content_sections>[string] => Boolean(section))
    : [];

  if (sections.length === 0) {
    return null;
  }

  const toSummaryParagraphs = (summary?: string, reason?: string) => {
    const content = (summary || reason || "요약이 아직 준비되지 않았습니다.").trim();
    return content
      .split(/(?<=[.!?])\s+/)
      .map((sentence) => sentence.trim())
      .filter(Boolean);
  };

  return (
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
                <article key={highlight.news_id} className="overflow-hidden rounded-md border border-line bg-white p-4">
                  <div className="flex items-start gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-background text-xs font-bold text-muted">
                      {highlightIndex + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-xs font-semibold text-accent">{highlight.source}</p>
                        <span className="text-xs text-muted">{highlight.reason}</span>
                      </div>
                      <h3 className="mt-2 break-words text-lg font-semibold leading-7">
                        {highlight.title_ko || highlight.title}
                      </h3>
                      {highlight.title_ko && highlight.title_ko !== highlight.title ? (
                        <p className="mt-1 break-words text-xs text-muted">원문: {highlight.title}</p>
                      ) : null}
                      <div className="mt-3 space-y-2 text-sm leading-7 text-muted">
                        {toSummaryParagraphs(highlight.summary, highlight.reason)
                          .filter(Boolean)
                          .map((sentence, sentenceIndex) => (
                            <p key={`${highlight.news_id}-${sentenceIndex}`}>{sentence.trim()}</p>
                          ))}
                      </div>
                      <div className="mt-4">
                        <a
                          href={highlight.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm font-semibold text-text transition hover:border-accent hover:bg-accentSoft"
                        >
                          원문 보기
                          <Icon name="arrowRight" className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
