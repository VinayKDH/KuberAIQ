"use client";

import { CalendarClock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useComplianceCalendar } from "@/features/compliance/hooks";
import {
  COMPLIANCE_CATEGORY_LABELS,
  COMPLIANCE_COPY,
  COMPLIANCE_STATUS_LABELS,
  COMPLIANCE_STATUS_VARIANTS,
} from "@/lib/constants";
import { formatDate } from "@/lib/format";

export function ComplianceCalendarPanel() {
  const { data, isLoading, isError } = useComplianceCalendar(90);

  if (isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }

  if (isError || !data) {
    return <p className="text-sm text-destructive">Failed to load compliance calendar.</p>;
  }

  if (!data.profile_complete) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{COMPLIANCE_COPY.CALENDAR_TITLE}</CardTitle>
        </div>
        <CardDescription>Deadlines in the next {data.days} days</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {data.events.length ? (
          data.events.map((event) => (
            <div key={`${event.obligation_id}-${event.period_key}`} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3">
              <div>
                <p className="font-medium">{event.title}</p>
                <p className="text-sm text-muted-foreground">
                  {COMPLIANCE_CATEGORY_LABELS[event.category] ?? event.category} · Due {formatDate(event.due_date)}
                </p>
              </div>
              <Badge variant={COMPLIANCE_STATUS_VARIANTS[event.status] ?? "secondary"}>
                {COMPLIANCE_STATUS_LABELS[event.status] ?? event.status}
              </Badge>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No upcoming deadlines in this window.</p>
        )}
      </CardContent>
    </Card>
  );
}
