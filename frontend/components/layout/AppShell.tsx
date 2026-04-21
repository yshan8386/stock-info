"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { Icon } from "@/components/ui/Icon";

const navItems = [
  { href: "/", label: "홈", icon: "home" },
  { href: "/brief", label: "데일리", icon: "newspaper" },
  { href: "/backtest", label: "백테스트", icon: "chart" },
  { href: "/position", label: "투자 현황", icon: "briefcase" },
  { href: "/glossary", label: "개념", icon: "book" },
  { href: "/settings/profile", label: "설정", icon: "settings" }
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  async function logout() {
    await apiFetch("/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  if (isAuthPage) {
    return <main className="min-h-screen bg-background text-text">{children}</main>;
  }

  return (
    <div className="min-h-screen bg-background pb-20 text-text md:pb-0">
      <aside className="fixed left-0 top-0 hidden h-screen w-24 border-r border-line bg-white md:flex md:flex-col md:items-center md:py-5">
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
                className={`flex h-12 w-12 items-center justify-center rounded-md transition ${
                  active ? "bg-accent text-white" : "text-muted hover:bg-accentSoft hover:text-accent"
                }`}
                aria-label={item.label}
              >
                <Icon name={item.icon} className="h-5 w-5" />
              </Link>
            );
          })}
        </nav>
        <button className="text-xs text-muted hover:text-text" onClick={logout}>
          로그아웃
        </button>
      </aside>

      <header className="sticky top-0 z-10 border-b border-line bg-white/90 px-5 py-4 backdrop-blur md:ml-24">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/" className="text-lg font-bold">
            ysj.brief
          </Link>
          <div className="text-sm text-muted">개인 투자 대시보드</div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 py-6 md:ml-24 md:px-8">{children}</main>

      <nav className="fixed bottom-0 left-0 right-0 grid grid-cols-6 border-t border-line bg-white md:hidden">
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
              <Icon name={item.icon} className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
