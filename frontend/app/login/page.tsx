"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          username: form.get("username"),
          password: form.get("password")
        })
      });
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5">
      <Card className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="text-3xl font-bold text-accent">ysj.brief</div>
          <p className="mt-2 text-sm text-muted">개인 투자 대시보드</p>
        </div>
        <form className="space-y-4" onSubmit={submit}>
          <Input label="아이디" name="username" autoComplete="username" required />
          <Input label="비밀번호" name="password" type="password" autoComplete="current-password" required />
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <Button className="w-full" disabled={loading}>
            {loading ? "로그인 중" : "로그인"}
          </Button>
        </form>
        <Link className="mt-5 block text-center text-sm text-accent" href="/signup">
          계정이 없으신가요?
        </Link>
      </Card>
    </div>
  );
}
