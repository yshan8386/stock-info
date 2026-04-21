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
  const [selectedCategory, setSelectedCategory] = useState("all");
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
    const categoryFiltered =
      selectedCategory === "all" ? groups : groups.filter((group) => group.category.slug === selectedCategory);
    if (!query.trim()) return categoryFiltered;
    return groups
      .filter((group) => selectedCategory === "all" || group.category.slug === selectedCategory)
      .map((group) => ({
        ...group,
        terms: group.terms.filter((term) => `${term.term_ko} ${term.term_en ?? ""}`.toLowerCase().includes(query.toLowerCase()))
      }))
      .filter((group) => group.terms.length > 0);
  }, [groups, query, selectedCategory]);

  const totalTerms = groups.reduce((sum, group) => sum + group.terms.length, 0);
  const visibleTerms = filtered.reduce((sum, group) => sum + group.terms.length, 0);

  return (
    <div className="space-y-6">
      <div className="surface rounded-md p-6">
        <div>
          <p className="text-sm font-semibold text-accent">로그인 없이 검색할 수 있습니다</p>
          <h1 className="mt-1 text-3xl font-bold">투자 개념 정리</h1>
          <p className="mt-2 max-w-2xl leading-7 text-muted">지표, 성과, 매매 전략 용어를 DB에서 불러와 정리합니다. 영어 약어나 지표명으로도 검색할 수 있습니다.</p>
        </div>
        <div className="mt-5 inline-flex rounded-md border border-line bg-white px-3 py-2 text-sm text-muted">
          카테고리 {groups.length}개 · 개념 {totalTerms}개
        </div>
      </div>

      <Card className="space-y-4">
        <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
          <Input label="검색" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="예: MDD, RSI, PER" />
          {query ? (
            <button className="rounded-md border border-line px-4 py-3 text-sm font-semibold text-muted transition hover:border-accent hover:text-text" onClick={() => setQuery("")}>
              검색 지우기
            </button>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className={`rounded-md px-3 py-2 text-sm font-semibold transition ${
              selectedCategory === "all" ? "bg-text text-white" : "border border-line bg-white text-muted hover:border-accent hover:text-text"
            }`}
            onClick={() => setSelectedCategory("all")}
          >
            전체
          </button>
          {groups.map((group) => (
            <button
              key={group.category.id}
              className={`rounded-md px-3 py-2 text-sm font-semibold transition ${
                selectedCategory === group.category.slug
                  ? "bg-text text-white"
                  : "border border-line bg-white text-muted hover:border-accent hover:text-text"
              }`}
              onClick={() => setSelectedCategory(group.category.slug)}
            >
              {group.category.name}
            </button>
          ))}
        </div>
        <p className="text-sm text-muted">현재 {visibleTerms}개 개념을 보고 있습니다.</p>
      </Card>

      {loading ? <Card className="text-muted">투자 개념을 불러오는 중입니다.</Card> : null}
      {error ? <Card className="border-red-200 bg-red-50 text-red-700">{error}</Card> : null}
      <div className="space-y-6">
        {filtered.map((group) => (
          <section key={group.category.id} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="flex items-center gap-2 text-lg font-semibold">
                <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accentSoft text-accent">
                  <Icon name={glossaryIconName(group.category.slug)} className="h-5 w-5" />
                </span>
                {group.category.name}
              </h2>
              <span className="rounded-md bg-white px-2.5 py-1 text-xs text-muted">{group.terms.length}개</span>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {group.terms.map((term) => (
                <Link key={term.id} href={`/glossary/${term.id}`}>
                  <Card className="h-full transition hover:-translate-y-0.5 hover:border-accent hover:bg-accentSoft/50">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="font-semibold">
                        {term.term_ko} {term.term_en ? <span className="text-muted">({term.term_en})</span> : null}
                      </h3>
                      <Icon name="arrowRight" className="h-4 w-4 shrink-0 text-muted" />
                    </div>
                    <p className="mt-2 text-sm text-muted">{term.short_desc}</p>
                    {term.formula ? <p className="mt-3 line-clamp-1 rounded-md bg-background px-2.5 py-1.5 text-xs text-muted">{term.formula}</p> : null}
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
