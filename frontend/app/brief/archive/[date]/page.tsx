"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { BriefingSections } from "@/components/brief/BriefingSections";
import { Card } from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type { Briefing } from "@/types/api";

export default function ArchiveDetailPage({
  params,
  searchParams
}: {
  params: Promise<{ date: string }>;
  searchParams: Promise<{ type?: string }>;
}) {
  const { date } = use(params);
  const { type } = use(searchParams);
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const query = type ? `?briefing_type=${encodeURIComponent(type)}` : "";
    apiFetch<Briefing>(`/brief/date/${date}${query}`)
      .then(setBriefing)
      .catch(() => setBriefing(null))
      .finally(() => setLoading(false));
  }, [date, type]);

  return (
    <div className="font-briefing space-y-5">
      <Link href="/brief/archive" className="text-sm text-muted">
        ← 아카이브
      </Link>
      <Card>
        {loading ? (
          <p className="text-muted">브리핑을 불러오는 중입니다.</p>
        ) : briefing ? (
          briefing.content_sections ? (
            <div className="space-y-5">
              <div className="rounded-md bg-panel p-4">
                <p className="text-sm font-semibold text-accent">{briefing.one_liner}</p>
                <p className="mt-2 text-xs text-muted">{new Date(briefing.generated_at).toLocaleString("ko-KR")}</p>
              </div>
              <BriefingSections briefing={briefing} />
            </div>
          ) : (
            <div className="prose-brief">
              <ReactMarkdown>{briefing.content_markdown}</ReactMarkdown>
            </div>
          )
        ) : (
          <p className="text-muted">브리핑을 찾을 수 없습니다.</p>
        )}
      </Card>
    </div>
  );
}
