import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_PATHS = ["/glossary"];
const AUTH_ONLY_PATHS = ["/login", "/signup"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isPublic = PUBLIC_PATHS.some((path) => pathname.startsWith(path));
  const isAuthOnly = AUTH_ONLY_PATHS.some((path) => pathname.startsWith(path));
  const hasToken = request.cookies.has("access_token");

  if (!hasToken && !isPublic && !isAuthOnly) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
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
