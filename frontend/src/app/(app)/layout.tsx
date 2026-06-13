"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { API_PATHS, ROUTES } from "@/lib/constants";
import { apiClient } from "@/lib/api-client";
import { clearSession, isAuthenticated } from "@/lib/auth";
import { resolveProtectedRoute, type MeGate } from "@/lib/session-routing";

interface MeResponse extends MeGate {
  user: { role: string; email: string; full_name: string | null; company_id: string | null };
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace(ROUTES.LOGIN);
      return;
    }

    apiClient<MeResponse>(API_PATHS.ME)
      .then((me) => {
        const redirect = resolveProtectedRoute({ ...me, role: me.user.role }, pathname);
        if (redirect) {
          router.replace(redirect);
          return;
        }
        setReady(true);
      })
      .catch(() => {
        clearSession();
        router.replace(ROUTES.LOGIN);
      });
  }, [pathname, router]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
