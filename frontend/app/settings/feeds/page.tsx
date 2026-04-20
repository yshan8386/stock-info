"use client";

import { useEffect, useState } from "react";

import { Card } from "@/components/ui/Card";
import { apiFetch } from "@/lib/api";
import type { Feed } from "@/types/api";

export default function FeedSettingsPage() {
  const [feeds, setFeeds] = useState<Feed[]>([]);

  useEffect(() => {
    apiFetch<Feed[]>("/feeds").then(setFeeds).catch(() => setFeeds([]));
  }, []);

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">RSS 피드 관리</h1>
      <div className="grid gap-3">
        {feeds.map((feed) => (
          <Card key={feed.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-semibold">{feed.name}</h2>
                <p className="mt-1 break-all text-sm text-muted">{feed.url}</p>
              </div>
              <span className={feed.is_active ? "text-accent" : "text-muted"}>
                {feed.is_active ? "활성" : "비활성"}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

