"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";

const navItems = [
  { href: "/", label: "홈", icon: "🏠" },
  { href: "/brief", label: "데일리", icon: "📰" },
  { href: "/backtest", label: "백테스트", icon: "📊" },
  { href: "/position", label: "투자 현황", icon: "💼" },
  { href: "/glossary", label: "개념", icon: "📖" },
  { href: "/settings/profile", label: "설정", icon: "⚙️" }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  if (isAuthPage) {
    return <main className="min-h-screen bg-background">{children}</main>;
  }

  return (
    <div className="min-h-screen bg-background pb-20 text-text md:pb-0">
      <aside className="fixed left-0 top-0 hidden h-screen w-24 border-r border-line bg-[#0d1010] md:flex md:flex-col md:items-center md:py-5">
        <Link href="/" className="mb-8 text-xl font-bold text-accent">
          ysj
        </Link>
        <nav className="flex flex-1 flex-col gap-2">
          {navItems.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex h-12 w-12 items-center justify-center rounded-md text-xl ${
                  active ? "bg-accent text-[#07110d]" : "text-muted hover:bg-panel hover:text-text"
                }`}
                aria-label={item.label}
              >
                {item.icon}
              </Link>
            );
          })}
        </nav>
        <button className="text-xs text-muted hover:text-text" onClick={logout}>
          로그아웃
        </button>
      </aside>

      <header className="sticky top-0 z-10 border-b border-line bg-background/95 px-5 py-4 backdrop-blur md:ml-24">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/" className="text-lg font-bold">
            ysj.brief
          </Link>
          <div className="text-sm text-muted">개인 투자 대시보드</div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-6 md:ml-24 md:px-8">{children}</main>

      <nav className="fixed bottom-0 left-0 right-0 grid grid-cols-6 border-t border-line bg-[#0d1010] md:hidden">
        {navItems.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 px-1 py-2 text-xs ${
                active ? "text-accent" : "text-muted"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

