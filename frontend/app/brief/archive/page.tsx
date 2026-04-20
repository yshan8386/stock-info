"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { apiFetch, formatDate } from "@/lib/api";
import type { BriefingArchiveItem } from "@/types/api";

export default function ArchivePage() {
  const [items, setItems] = useState<BriefingArchiveItem[]>([]);

  useEffect(() => {
    apiFetch<BriefingArchiveItem[]>("/brief/archive").then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div className="space-y-5">
      <div>
        <Link href="/brief" className="text-sm text-muted">
          ← 오늘
        </Link>
        <h1 className="mt-3 text-2xl font-bold">브리핑 아카이브</h1>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <Link key={item.id} href={`/brief/archive/${item.briefing_date}`}>
            <Card className="transition hover:border-accent">
              <p className="text-sm text-muted">{formatDate(item.briefing_date)}</p>
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

