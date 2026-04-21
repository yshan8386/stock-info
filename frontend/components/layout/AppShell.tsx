"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { Icon } from "@/components/ui/Icon";
import type { User } from "@/types/api";

const navItems = [
  { href: "/", label: "홈", icon: "home", access: "public" },
  { href: "/brief", label: "데일리 브리핑", icon: "newspaper", access: "public" },
  { href: "/glossary", label: "투자 개념", icon: "book", access: "public" },
  { href: "/backtest", label: "백테스트", icon: "chart", access: "private" },
  { href: "/position", label: "투자 현황", icon: "briefcase", access: "private" },
  { href: "/settings/profile", label: "설정", icon: "settings", access: "private" }
] as const;

const pageTitles: Record<string, string> = {
  "/": "홈",
  "/brief": "데일리 브리핑",
  "/glossary": "투자 개념 정리",
  "/backtest": "백테스트",
  "/position": "투자 현황",
  "/settings/profile": "설정"
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = pathname === "/login" || pathname === "/signup";
  const [user, setUser] = useState<User | null>(null);
  const currentTitle =
    navItems.find((item) => pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href)))?.label ??
    pageTitles[pathname] ??
    "ysj.brief";

  useEffect(() => {
    if (isAuthPage) return;
    apiFetch<User>("/auth/me")
      .then(setUser)
      .catch(() => setUser(null));
  }, [isAuthPage]);

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    setUser(null);
    router.replace("/login");
  }

  if (isAuthPage) {
    return <main className="min-h-screen bg-background text-text">{children}</main>;
  }

  return (
    <div className="min-h-screen bg-background pb-20 text-text md:pb-0">
      <aside className="fixed left-0 top-0 hidden h-screen w-64 border-r border-line bg-white/88 px-4 py-5 shadow-sm backdrop-blur md:flex md:flex-col">
        <Link href="/" className="mb-8 flex items-center gap-3 rounded-md px-2 py-1">
          <span className="flex h-10 w-10 items-center justify-center rounded-md bg-text text-sm font-bold text-white">YSJ</span>
          <span>
            <span className="block text-base font-bold">ysj.brief</span>
            <span className="text-xs text-muted">투자 정보 허브</span>
          </span>
        </Link>
        <nav className="flex flex-1 flex-col gap-5">
          {(["public", "private"] as const).map((access) => (
            <div key={access} className="space-y-1.5">
              <p className="px-3 text-xs font-semibold text-muted">{access === "public" ? "바로 보기" : "로그인 후 이용"}</p>
              {navItems
                .filter((item) => item.access === access)
                .map((item) => {
                  const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center justify-between gap-3 rounded-md px-3 py-3 text-sm font-semibold transition ${
                        active ? "bg-text text-white shadow-sm" : "text-muted hover:bg-accentSoft hover:text-text"
                      }`}
                      aria-label={item.label}
                    >
                      <span className="flex items-center gap-3">
                        <Icon name={item.icon} className="h-5 w-5" />
                        <span>{item.label}</span>
                      </span>
                      {item.access === "private" && !user ? (
                        <span className={`text-[11px] ${active ? "text-white/75" : "text-muted"}`}>로그인</span>
                      ) : null}
                    </Link>
                  );
                })}
            </div>
          ))}
        </nav>
        <div className="rounded-md border border-line bg-panel p-3 text-sm">
          {user ? (
            <>
              <p className="font-semibold">{user.display_name}</p>
              <p className="mt-1 text-xs text-muted">개인 기능을 사용할 수 있습니다.</p>
              <button className="mt-2 text-sm font-semibold text-muted hover:text-text" onClick={logout}>
                로그아웃
              </button>
            </>
          ) : (
            <div className="grid gap-2">
              <Link className="rounded-md bg-text px-3 py-2 text-center font-semibold text-white" href="/login">
                로그인
              </Link>
              <Link className="rounded-md border border-line px-3 py-2 text-center font-semibold text-text" href="/signup">
                회원가입
              </Link>
            </div>
          )}
        </div>
      </aside>

      <header className="sticky top-0 z-10 border-b border-line bg-white/88 px-5 py-4 backdrop-blur md:ml-64">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div>
            <Link href="/" className="text-lg font-bold">
              ysj.brief
            </Link>
            <p className="text-xs text-muted md:hidden">{currentTitle}</p>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {user ? (
              <button className="font-semibold text-muted hover:text-text" onClick={logout}>
                로그아웃
              </button>
            ) : (
              <>
                <Link className="font-semibold text-muted hover:text-text" href="/login">
                  로그인
                </Link>
                <Link className="rounded-md bg-text px-3 py-2 font-semibold text-white" href="/signup">
                  가입
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-6 md:ml-64 md:px-8">{children}</main>

      <nav className="fixed bottom-0 left-0 right-0 grid grid-cols-6 border-t border-line bg-white/95 backdrop-blur md:hidden">
        {navItems.slice(0, 5).map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 px-1 py-2 text-xs ${
                active ? "text-accent" : "text-muted"
              }`}
            >
              <Icon name={item.icon} className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
