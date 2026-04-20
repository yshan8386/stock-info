"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type { Briefing } from "@/types/api";

export default function BriefPage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(false);

  async function load() {
    const data = await apiFetch<Briefing>("/brief/today");
    setBriefing(data);
  }

  async function regenerate() {
    setLoading(true);
    try {
      const data = await apiFetch<Briefing>("/brief/regenerate", { method: "POST" });
      setBriefing(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load().catch(() => setBriefing(null));
  }, []);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">데일리 브리핑</h1>
          <p className="mt-1 text-sm text-muted">오늘의 개발, 투자, AI 이슈</p>
        </div>
        <div className="flex gap-2">
          <Link className="rounded-md border border-line px-4 py-3 text-sm" href="/brief/archive">
            아카이브
          </Link>
          <Button onClick={regenerate} disabled={loading}>
            {loading ? "생성 중" : "재생성"}
          </Button>
        </div>
      </div>

      <Card>
        {briefing ? (
          <>
            <div className="mb-6 flex flex-wrap gap-2 text-xs text-muted">
              <span>기반 기사 {briefing.source_article_count ?? 0}건</span>
              <span>모델 {briefing.model_used ?? "mock"}</span>
              <span>{new Date(briefing.generated_at).toLocaleString("ko-KR")}</span>
            </div>
            <div className="prose-brief">
              <ReactMarkdown>{briefing.content_markdown}</ReactMarkdown>
            </div>
          </>
        ) : (
          <p className="text-muted">브리핑을 불러오는 중입니다.</p>
        )}
      </Card>
    </div>
  );
}

