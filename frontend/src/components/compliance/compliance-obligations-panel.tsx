"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useCompleteComplianceObligation,
} from "@/features/compliance/hooks";
import type { ComplianceObligation } from "@/features/compliance/types";
import {
  COMPLIANCE_CATEGORY_LABELS,
  COMPLIANCE_COPY,
  COMPLIANCE_STATUS_LABELS,
  COMPLIANCE_STATUS_VARIANTS,
} from "@/lib/constants";
import { formatDate } from "@/lib/format";

interface ComplianceObligationsPanelProps {
  obligationsByCategory: Record<string, ComplianceObligation[]>;
  notApplicable: Array<{ id: string; category: string; title: string; reason: string }>;
}

export function ComplianceObligationsPanel({
  obligationsByCategory,
  notApplicable,
}: ComplianceObligationsPanelProps) {
  const completeMutation = useCompleteComplianceObligation();

  const handleComplete = (obligation: ComplianceObligation) => {
    completeMutation.mutate({
      obligationId: obligation.id,
      periodKey: obligation.period_key,
    });
  };

  return (
    <div className="space-y-6">
      {Object.entries(obligationsByCategory).map(([category, items]) => (
        <Card key={category}>
          <CardHeader>
            <CardTitle>{COMPLIANCE_CATEGORY_LABELS[category] ?? category}</CardTitle>
            <CardDescription>{items.length} applicable obligation(s)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {items.map((obligation) => (
              <div key={`${obligation.id}-${obligation.period_key}`} className="rounded-md border p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-medium">{obligation.title}</p>
                      <Badge variant={COMPLIANCE_STATUS_VARIANTS[obligation.status] ?? "secondary"}>
                        {COMPLIANCE_STATUS_LABELS[obligation.status] ?? obligation.status}
                      </Badge>
                      <Badge variant="outline">{obligation.frequency}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{obligation.description}</p>
                    <p className="text-sm text-muted-foreground">
                      Due {formatDate(obligation.due_date)} · Period {obligation.period_key}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {obligation.status !== "COMPLETED" && (
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={completeMutation.isPending}
                        onClick={() => handleComplete(obligation)}
                      >
                        {COMPLIANCE_COPY.MARK_COMPLETE}
                      </Button>
                    )}
                    {obligation.action_route && (
                      <Link
                        href={obligation.action_route}
                        className="inline-flex h-9 items-center rounded-md border border-input bg-background px-3 text-sm hover:bg-accent"
                      >
                        {COMPLIANCE_COPY.LEARN_MORE}
                        <ExternalLink className="ml-1 h-3 w-3" />
                      </Link>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ))}

      {notApplicable.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>{COMPLIANCE_COPY.NOT_APPLICABLE_TITLE}</CardTitle>
            <CardDescription>Obligations that do not apply to your current profile</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {notApplicable.map((item) => (
              <div key={item.id} className="rounded-md border border-dashed p-3 text-sm">
                <p className="font-medium">{item.title}</p>
                <p className="text-muted-foreground">{item.reason}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
