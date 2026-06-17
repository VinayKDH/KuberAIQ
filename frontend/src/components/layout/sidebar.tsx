"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bot,
  ClipboardList,
  FileText,
  IndianRupee,
  LayoutDashboard,
  Package,
  Settings,
  ShieldCheck,
  Users,
} from "lucide-react";
import { APP_NAME, NAV_ITEMS, NAV_ITEMS_CA, ROUTES, USER_ROLE } from "@/lib/constants";
import { getStoredUser } from "@/lib/auth";
import { getPreferredLanguage, I18N_MESSAGES } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const iconMap = {
  LayoutDashboard,
  FileText,
  ClipboardList,
  Package,
  Users,
  IndianRupee,
  Bot,
  ShieldCheck,
  Settings,
} as const;

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const user = getStoredUser();
  const navItems = user?.role === USER_ROLE.CA ? NAV_ITEMS_CA : NAV_ITEMS;
  const homeHref = user?.role === USER_ROLE.CA ? ROUTES.CA_DASHBOARD : ROUTES.DASHBOARD;
  const i18n = I18N_MESSAGES[getPreferredLanguage()];

  return (
    <aside className="flex h-full w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 items-center border-b border-sidebar-border px-6">
        <Link href={homeHref} className="flex items-center gap-2 font-semibold" onClick={onNavigate}>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
            K
          </div>
          <span>{APP_NAME}</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = iconMap[item.icon as keyof typeof iconMap];
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-sidebar-border p-4">
        <p className="text-xs text-muted-foreground">
          {user?.role === USER_ROLE.CA ? i18n.sidebarFooterCa : i18n.sidebarFooterMsme}
        </p>
      </div>
    </aside>
  );
}
