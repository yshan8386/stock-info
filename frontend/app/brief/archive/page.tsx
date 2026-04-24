"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { apiFetch, formatDate } from "@/lib/api";
import type { BriefingArchiveItem } from "@/types/api";

const briefingTypeLabels: Record<string, string> = {
  daily_morning: "아침",
  daily_afternoon: "오후"
};

export default function ArchivePage() {
  const [items, setItems] = useState<BriefingArchiveItem[]>([]);

  useEffect(() => {
    apiFetch<BriefingArchiveItem[]>("/brief/archive").then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div className="font-briefing space-y-5">
      <div>
        <Link href="/brief" className="text-sm text-muted">
          ← 오늘
        </Link>
        <h1 className="mt-3 text-2xl font-bold">브리핑 아카이브</h1>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <Link key={item.id} href={`/brief/archive/${item.briefing_date}?type=${item.briefing_type}`}>
            <Card className="transition hover:border-accent">
              <div className="flex flex-wrap items-center gap-2 text-sm text-muted">
                <span>{formatDate(item.briefing_date)}</span>
                <span className="rounded-md bg-accentSoft px-2 py-0.5 text-xs font-semibold text-accent">
                  {briefingTypeLabels[item.briefing_type] ?? "데일리"}
                </span>
              </div>
              <h2 className="mt-2 text-lg font-semibold">{item.title}</h2>
              <p className="mt-2 text-muted">{item.one_liner}</p>
            </Card>
          </Link>
        ))}
        {items.length === 0 ? <Card className="text-muted">아직 저장된 브리핑이 없습니다.</Card> : null}
      </div>
    </div>
  );
}
