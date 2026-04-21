"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { LoadingBar } from "@/components/ui/LoadingBar";
import { apiFetch } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      await apiFetch("/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          username: form.get("username"),
          password: form.get("password"),
          password_confirm: form.get("password_confirm"),
          display_name: form.get("display_name"),
          phone: form.get("phone"),
          email: form.get("email")
        })
      });
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "회원가입에 실패했습니다");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-5 py-8">
      <Card className="w-full max-w-lg">
        <div className="mb-6">
          <Link href="/login" className="text-sm text-muted">
            ← 로그인
          </Link>
          <h1 className="mt-4 text-2xl font-bold">회원가입</h1>
        </div>
        {loading ? (
          <div className="mb-5">
            <LoadingBar active label="회원가입 정보를 확인하고 계정을 만들고 있습니다." />
          </div>
        ) : null}
        <form className="grid gap-4" onSubmit={submit}>
          <Input label="아이디" name="username" minLength={4} maxLength={20} required />
          <Input label="비밀번호" name="password" type="password" minLength={8} required />
          <Input label="비밀번호 확인" name="password_confirm" type="password" minLength={8} required />
          <Input label="닉네임" name="display_name" minLength={2} maxLength={20} required />
          <Input label="핸드폰 번호" name="phone" placeholder="010-1234-5678" required />
          <Input label="이메일" name="email" type="email" required />
          {error ? <p className="text-sm text-red-600">{error}</p> : null}
          <Button disabled={loading}>{loading ? "가입 중" : "가입하기"}</Button>
        </form>
      </Card>
    </div>
  );
}
