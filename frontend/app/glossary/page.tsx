"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Card } from "@/components/ui/Card";
import { Icon, glossaryIconName } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/api";
import type { GlossaryGroup } from "@/types/api";

export default function GlossaryPage() {
  const [groups, setGroups] = useState<GlossaryGroup[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<GlossaryGroup[]>("/glossary")
      .then((data) => {
        setGroups(data);
        setError("");
      })
      .catch((err) => {
        setGroups([]);
        setError(err instanceof Error ? err.message : "투자 개념을 불러오지 못했습니다");
      })
      .finally(() => setLoading(false));
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

  const totalTerms = groups.reduce((sum, group) => sum + group.terms.length, 0);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">투자 개념 정리</h1>
          <p className="mt-1 text-muted">DB에서 불러온 투자 용어와 지표</p>
        </div>
        <div className="rounded-md border border-line bg-white px-3 py-2 text-sm text-muted">
          카테고리 {groups.length}개 · 개념 {totalTerms}개
        </div>
      </div>
      <Input label="검색" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="MDD, RSI, PER" />
      {loading ? <Card className="text-muted">투자 개념을 불러오는 중입니다.</Card> : null}
      {error ? <Card className="border-red-200 bg-red-50 text-red-700">{error}</Card> : null}
      <div className="space-y-5">
        {filtered.map((group) => (
          <section key={group.category.id} className="space-y-3">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accentSoft text-accent">
                <Icon name={glossaryIconName(group.category.slug)} className="h-5 w-5" />
              </span>
              {group.category.name}
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {group.terms.map((term) => (
                <Link key={term.id} href={`/glossary/${term.id}`}>
                  <Card className="h-full transition hover:border-accent hover:bg-accentSoft/50">
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
        {!loading && !error && filtered.length === 0 ? (
          <Card className="text-muted">검색 결과가 없습니다.</Card>
        ) : null}
      </div>
    </div>
  );
}
