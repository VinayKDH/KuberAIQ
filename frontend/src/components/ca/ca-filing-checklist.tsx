"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCaCompleteFiling, useCaSkipFiling } from "@/features/ca/hooks";
import type { CaFilingChecklistItem } from "@/features/ca/types";
import {
  CA_COPY,
  COMPLIANCE_STATUS_LABELS,
  COMPLIANCE_STATUS_VARIANTS,
} from "@/lib/constants";
import { formatDate } from "@/lib/format";

interface CaFilingChecklistProps {
  companyId: string;
  items: CaFilingChecklistItem[];
  profileComplete?: boolean;
}

export function CaFilingChecklist({
  companyId,
  items,
  profileComplete = true,
}: CaFilingChecklistProps) {
  const completeMutation = useCaCompleteFiling();
  const skipMutation = useCaSkipFiling();
  const pending = completeMutation.isPending || skipMutation.isPending;

  if (!profileComplete) {
    return (
      <p className="text-sm text-muted-foreground">{CA_COPY.FILING_CHECKLIST_EMPTY}</p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{CA_COPY.FILING_CHECKLIST_TITLE}</p>
      <ul className="space-y-2">
        {items.map((item) => {
          const actionable =
            item.status !== "COMPLETED" &&
            item.status !== "NOT_APPLICABLE" &&
            item.status !== "SKIPPED";
          return (
            <li
              key={item.obligation_id}
              className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-2 text-sm"
            >
              <div className="space-y-0.5">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium">{item.title}</span>
                  <Badge
                    variant={COMPLIANCE_STATUS_VARIANTS[item.status] ?? "secondary"}
                  >
                    {COMPLIANCE_STATUS_LABELS[item.status] ?? item.status}
                  </Badge>
                </div>
                {item.due_date && (
                  <p className="text-muted-foreground">
                    Due {formatDate(item.due_date)}
                  </p>
                )}
              </div>
              {actionable && (
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={pending}
                    onClick={() =>
                      completeMutation.mutate({
                        companyId,
                        obligationId: item.obligation_id,
                        periodKey: item.period_key,
                      })
                    }
                  >
                    {CA_COPY.FILING_MARK_COMPLETE}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={pending}
                    onClick={() =>
                      skipMutation.mutate({
                        companyId,
                        obligationId: item.obligation_id,
                        periodKey: item.period_key,
                      })
                    }
                  >
                    {CA_COPY.FILING_SKIP}
                  </Button>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
