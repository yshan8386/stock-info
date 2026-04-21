import { NextResponse, type NextRequest } from "next/server";

const PROTECTED_PATHS = ["/backtest", "/position", "/settings"];
const AUTH_ONLY_PATHS = ["/login", "/signup"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED_PATHS.some((path) => pathname.startsWith(path));
  const isAuthOnly = AUTH_ONLY_PATHS.some((path) => pathname.startsWith(path));
  const hasToken = request.cookies.has("access_token");

  if (!hasToken && isProtected) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  if (hasToken && isAuthOnly) {
    const url = request.nextUrl.clone();
    url.pathname = "/";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg).*)"]
};
