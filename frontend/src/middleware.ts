import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_WEB_URL = process.env.NEXT_PUBLIC_WEB_URL ?? "https://www.kuberaiq.com";
const PUBLIC_APEX_DOMAIN = process.env.NEXT_PUBLIC_APEX_DOMAIN ?? "kuberaiq.com";

export function middleware(request: NextRequest) {
  const host = request.headers.get("host")?.split(":")[0] ?? "";
  if (host !== PUBLIC_APEX_DOMAIN) {
    return NextResponse.next();
  }

  const canonical = new URL(PUBLIC_WEB_URL);
  const target = request.nextUrl.clone();
  target.protocol = canonical.protocol;
  target.host = canonical.host;
  return NextResponse.redirect(target, 308);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
