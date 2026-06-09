"use client";

import Link from "next/link";
import { AlertTriangle, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { COMPLIANCE_COPY, ROUTES } from "@/lib/constants";
import type { ComplianceSummary } from "@/features/compliance/types";

interface ComplianceOverviewProps {
  summary: ComplianceSummary;
  profileComplete: boolean;
}

export function ComplianceOverview({ summary, profileComplete }: ComplianceOverviewProps) {
  if (!profileComplete) {
    return (
      <Card className="border-amber-500/50 bg-amber-50/50 dark:bg-amber-950/20">
        <CardContent className="flex items-start gap-3 pt-6">
          <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
          <div>
            <p className="font-medium">{COMPLIANCE_COPY.PROFILE_INCOMPLETE}</p>
            <p className="text-sm text-muted-foreground">{COMPLIANCE_COPY.PROFILE_HINT}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        label={COMPLIANCE_COPY.HEALTH_SCORE}
        value={`${summary.health_score}%`}
        icon={<ShieldCheck className="h-4 w-4" />}
        highlight={summary.overdue > 0 ? "danger" : summary.due_this_week > 0 ? "warning" : "default"}
      />
      <MetricCard label={COMPLIANCE_COPY.OVERDUE} value={String(summary.overdue)} highlight={summary.overdue ? "danger" : "default"} />
      <MetricCard label={COMPLIANCE_COPY.DUE_THIS_WEEK} value={String(summary.due_this_week)} highlight={summary.due_this_week ? "warning" : "default"} />
      <MetricCard label="Tracked" value={`${summary.completed}/${summary.total_applicable}`} />
      {summary.overdue > 0 && (
        <Card className="border-destructive/50 sm:col-span-2 lg:col-span-4">
          <CardContent className="flex items-center justify-between gap-3 pt-6">
            <p className="text-sm text-destructive">
              {summary.overdue} obligation(s) overdue — review and mark complete after filing.
            </p>
            <Link href={ROUTES.SETTINGS} className="text-sm font-medium underline">
              Update profile
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon,
  highlight = "default",
}: {
  label: string;
  value: string;
  icon?: React.ReactNode;
  highlight?: "default" | "warning" | "danger";
}) {
  const border =
    highlight === "danger"
      ? "border-destructive/40"
      : highlight === "warning"
        ? "border-amber-500/40"
        : "";
  return (
    <Card className={border}>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          {icon}
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );
}
