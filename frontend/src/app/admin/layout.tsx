"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { ADMIN_COPY, ADMIN_PAGE_TITLES, ROUTES } from "@/lib/constants";
import { isAdminAuthenticated } from "@/lib/admin-auth";
import { AdminShell } from "@/components/admin/admin-shell";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const isLogin = pathname === ROUTES.ADMIN_LOGIN;

  useEffect(() => {
    const authed = isAdminAuthenticated();
    if (!isLogin && !authed) {
      router.replace(ROUTES.ADMIN_LOGIN);
      return;
    }
    if (isLogin && authed) {
      router.replace(ROUTES.ADMIN_DASHBOARD);
      return;
    }
    setReady(true);
  }, [isLogin, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-400">
        {ADMIN_COPY.LOADING}
      </div>
    );
  }

  if (isLogin) {
    return <>{children}</>;
  }

  const title =
    Object.entries(ADMIN_PAGE_TITLES).find(([route]) => pathname.startsWith(route))?.[1] ??
    ADMIN_COPY.PORTAL_TITLE;

  return <AdminShell title={title}>{children}</AdminShell>;
}
