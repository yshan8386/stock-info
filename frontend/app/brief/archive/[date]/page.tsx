"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { Card } from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type { Briefing } from "@/types/api";

export default function ArchiveDetailPage({ params }: { params: { date: string } }) {
  const [briefing, setBriefing] = useState<Briefing | null>(null);

  useEffect(() => {
    apiFetch<Briefing>(`/brief/date/${params.date}`).then(setBriefing).catch(() => setBriefing(null));
  }, [params.date]);

  return (
    <div className="space-y-5">
      <Link href="/brief/archive" className="text-sm text-muted">
        ← 아카이브
      </Link>
      <Card>
        {briefing ? (
          <div className="prose-brief">
            <ReactMarkdown>{briefing.content_markdown}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-muted">브리핑을 찾을 수 없습니다.</p>
        )}
      </Card>
    </div>
  );
}

