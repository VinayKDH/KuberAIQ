"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Bot,
  Building2,
  LayoutDashboard,
  LogOut,
  ScrollText,
  Server,
  Shield,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ADMIN_COPY, NAV_ITEMS_ADMIN, ROUTES } from "@/lib/constants";
import { clearAdminSession } from "@/lib/admin-auth";
import { cn } from "@/lib/utils";

const ICONS = {
  LayoutDashboard,
  Building2,
  Users,
  Bot,
  Server,
  ScrollText,
} as const;

export function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();

  function handleSignOut() {
    clearAdminSession();
    router.replace(ROUTES.ADMIN_LOGIN);
  }

  return (
    <aside className="flex h-full w-64 flex-col border-r border-zinc-800 bg-zinc-950 text-zinc-100">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-5">
        <Shield className="h-6 w-6 text-emerald-400" />
        <div>
          <p className="text-sm font-semibold">{ADMIN_COPY.PORTAL_TITLE}</p>
          <p className="text-xs text-zinc-400">{ADMIN_COPY.PORTAL_SUBTITLE}</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {NAV_ITEMS_ADMIN.map((item) => {
          const Icon = ICONS[item.icon as keyof typeof ICONS] ?? LayoutDashboard;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-zinc-800 p-3">
        <Button
          variant="ghost"
          className="w-full justify-start text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
          onClick={handleSignOut}
        >
          <LogOut className="mr-2 h-4 w-4" />
          {ADMIN_COPY.SIGN_OUT}
        </Button>
      </div>
    </aside>
  );
}

export function AdminShell({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="flex min-h-screen bg-zinc-900 text-zinc-100">
      <AdminSidebar />
      <div className="flex flex-1 flex-col">
        <header className="border-b border-zinc-800 bg-zinc-950 px-6 py-4">
          <h1 className="text-lg font-semibold">{title}</h1>
        </header>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
