"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { Card } from "@/components/ui/Card";
import { Icon, glossaryIconName } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api";
import type { GlossaryTerm } from "@/types/api";

export default function GlossaryDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [term, setTerm] = useState<GlossaryTerm | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch<GlossaryTerm>(`/glossary/${id}`)
      .then(setTerm)
      .catch(() => setTerm(null))
      .finally(() => setLoading(false));
  }, [id]);

  return (
    <div className="space-y-5">
      <Link href="/glossary" className="text-sm text-muted">
        ← 투자 개념 정리
      </Link>
      <Card>
        {loading ? (
          <p className="text-muted">개념을 불러오는 중입니다.</p>
        ) : term ? (
          <div className="space-y-6">
            <div>
              <p className="flex items-center gap-2 text-sm text-muted">
                <span className="flex h-8 w-8 items-center justify-center rounded-md bg-accentSoft text-accent">
                  <Icon name={glossaryIconName(term.category?.slug)} className="h-4 w-4" />
                </span>
                {term.category?.name}
              </p>
              <h1 className="mt-2 text-2xl font-bold">
                {term.term_ko} {term.term_en ? <span className="text-muted">({term.term_en})</span> : null}
              </h1>
            </div>
            <section>
              <h2 className="mb-2 font-semibold">한 줄 설명</h2>
              <p className="text-muted">{term.short_desc}</p>
            </section>
            {term.detail_markdown ? (
              <section className="prose-brief">
                <ReactMarkdown>{term.detail_markdown}</ReactMarkdown>
              </section>
            ) : null}
            {term.formula ? (
              <section>
                <h2 className="mb-2 font-semibold">수식</h2>
                <pre className="overflow-x-auto rounded-md border border-line bg-accentSoft p-4 text-sm text-accent">
                  {term.formula}
                </pre>
              </section>
            ) : null}
            {term.example ? (
              <section>
                <h2 className="mb-2 font-semibold">예시</h2>
                <p className="text-muted">{term.example}</p>
              </section>
            ) : null}
          </div>
        ) : (
          <p className="text-muted">개념을 찾을 수 없습니다.</p>
        )}
      </Card>
    </div>
  );
}
