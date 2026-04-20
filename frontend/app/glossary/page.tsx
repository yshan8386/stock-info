"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/api";
import type { GlossaryGroup } from "@/types/api";

export default function GlossaryPage() {
  const [groups, setGroups] = useState<GlossaryGroup[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    apiFetch<GlossaryGroup[]>("/glossary").then(setGroups).catch(() => setGroups([]));
  }, []);

  const filtered = useMemo(() => {
    if (!query.trim()) return groups;
    return groups
      .map((group) => ({
        ...group,
        terms: group.terms.filter((term) => `${term.term_ko} ${term.term_en ?? ""}`.toLowerCase().includes(query.toLowerCase()))
      }))
      .filter((group) => group.terms.length > 0);
  }, [groups, query]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">투자 개념 정리</h1>
        <p className="mt-1 text-muted">자주 쓰는 투자 용어와 지표</p>
      </div>
      <Input label="검색" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="MDD, RSI, PER" />
      <div className="space-y-5">
        {filtered.map((group) => (
          <section key={group.category.id} className="space-y-3">
            <h2 className="text-lg font-semibold">
              {group.category.icon} {group.category.name}
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {group.terms.map((term) => (
                <Link key={term.id} href={`/glossary/${term.id}`}>
                  <Card className="h-full transition hover:border-accent">
                    <h3 className="font-semibold">
                      {term.term_ko} {term.term_en ? <span className="text-muted">({term.term_en})</span> : null}
                    </h3>
                    <p className="mt-2 text-sm text-muted">{term.short_desc}</p>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

