"use client";

import { AlertTriangle, BadgeCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CA_COPY, CA_OVERDUE_ALERT_THRESHOLD } from "@/lib/constants";
import type { CaDashboardClient } from "@/features/ca/types";

interface CaClientHealthBadgesProps {
  client: CaDashboardClient;
}

export function CaClientHealthBadges({ client }: CaClientHealthBadgesProps) {
  const badges: Array<{ key: string; label: string; variant: "destructive" | "secondary" }> = [];

  if (!client.gstin) {
    badges.push({
      key: "gstin",
      label: CA_COPY.HEALTH_GSTIN_MISSING,
      variant: "destructive",
    });
  }

  if (client.profile_complete === false) {
    badges.push({
      key: "profile",
      label: CA_COPY.HEALTH_PROFILE_INCOMPLETE,
      variant: "destructive",
    });
  }

  if ((client.overdue_total ?? 0) >= CA_OVERDUE_ALERT_THRESHOLD) {
    badges.push({
      key: "overdue",
      label: CA_COPY.HEALTH_OVERDUE_HIGH,
      variant: "destructive",
    });
  }

  if ((client.filings_due_soon ?? 0) > 0) {
    badges.push({
      key: "due-soon",
      label: CA_COPY.HEALTH_FILINGS_DUE_SOON,
      variant: "secondary",
    });
  }

  if (client.risk_level === "high" && badges.length === 0) {
    badges.push({
      key: "at-risk",
      label: CA_COPY.HEALTH_AT_RISK,
      variant: "destructive",
    });
  }

  if (!badges.length) {
    return (
      <Badge variant="outline" className="gap-1 text-emerald-700">
        <BadgeCheck className="h-3 w-3" />
        Healthy
      </Badge>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5">
      {badges.map((badge) => (
        <Badge key={badge.key} variant={badge.variant} className="gap-1">
          <AlertTriangle className="h-3 w-3" />
          {badge.label}
        </Badge>
      ))}
    </div>
  );
}
