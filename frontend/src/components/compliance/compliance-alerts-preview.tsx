"use client";

import { Bell } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useComplianceAlertsPreview } from "@/features/compliance/hooks";
import {
  COMPLIANCE_CATEGORY_LABELS,
  COMPLIANCE_COPY,
  COMPLIANCE_STATUS_LABELS,
  COMPLIANCE_STATUS_VARIANTS,
} from "@/lib/constants";
import { formatDate } from "@/lib/format";

export function ComplianceAlertsPreviewPanel() {
  const { data, isLoading, isError, error } = useComplianceAlertsPreview();

  if (isLoading) {
    return <Skeleton className="h-24 w-full" />;
  }

  if (isError) {
    return (
      <p className="text-sm text-destructive">
        {error instanceof Error ? error.message : "Failed to load compliance alerts"}
      </p>
    );
  }

  if (!data) return null;

  return (
    <Card className="border-primary/20">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{COMPLIANCE_COPY.COMPLIANCE_ALERTS_PREVIEW}</CardTitle>
        </div>
        <CardDescription>
          Obligations due in the next {data.due_soon_days} days
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.count === 0 ? (
          <p className="text-sm text-muted-foreground">{COMPLIANCE_COPY.ALERTS_EMPTY}</p>
        ) : (
          data.alerts.map((alert) => (
            <div key={`${alert.id}-${alert.due_date}`} className="rounded-md border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium">{alert.title}</p>
                <Badge variant={COMPLIANCE_STATUS_VARIANTS[alert.status] ?? "secondary"}>
                  {COMPLIANCE_STATUS_LABELS[alert.status] ?? alert.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                {COMPLIANCE_CATEGORY_LABELS[alert.category] ?? alert.category} · Due{" "}
                {formatDate(alert.due_date)} · {alert.days_until_due} day
                {alert.days_until_due === 1 ? "" : "s"} left
              </p>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
