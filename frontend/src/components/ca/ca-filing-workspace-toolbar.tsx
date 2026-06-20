"use client";

import { useState } from "react";
import { Download, FileCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCaBulkCompleteFilings, useCaExportFilingCsv } from "@/features/ca/hooks";
import type { CaDashboardClient } from "@/features/ca/types";
import { CA_FILING_CHECKLIST_IDS, CA_WORKSPACE_COPY } from "@/lib/constants";

interface CaFilingWorkspaceToolbarProps {
  clients: CaDashboardClient[];
  dueBefore: string;
  onDueBeforeChange: (value: string) => void;
}

export function CaFilingWorkspaceToolbar({
  clients,
  dueBefore,
  onDueBeforeChange,
}: CaFilingWorkspaceToolbarProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const bulkComplete = useCaBulkCompleteFilings();
  const exportCsv = useCaExportFilingCsv();

  const toggleClient = (companyId: string) => {
    setSelectedIds((prev) =>
      prev.includes(companyId) ? prev.filter((id) => id !== companyId) : [...prev, companyId],
    );
  };

  return (
    <div className="space-y-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1">
          <Label htmlFor="due-before">{CA_WORKSPACE_COPY.FILTER_DUE_BEFORE}</Label>
          <Input
            id="due-before"
            type="date"
            value={dueBefore}
            onChange={(e) => onDueBeforeChange(e.target.value)}
          />
        </div>
        <Button
          variant="outline"
          disabled={exportCsv.isPending}
          onClick={() =>
            exportCsv.mutate({
              dueBefore: dueBefore || undefined,
            })
          }
        >
          <Download className="mr-2 h-4 w-4" />
          {CA_WORKSPACE_COPY.EXPORT_FILING_CSV}
        </Button>
        <Button
          disabled={!selectedIds.length || bulkComplete.isPending}
          onClick={() =>
            bulkComplete.mutate({
              companyIds: selectedIds,
              obligationIds: [...CA_FILING_CHECKLIST_IDS],
            })
          }
        >
          <FileCheck className="mr-2 h-4 w-4" />
          {CA_WORKSPACE_COPY.BULK_MARK_FILED} ({selectedIds.length})
        </Button>
      </div>
      {clients.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {clients.map((client) => (
            <label
              key={client.company_id}
              className="flex cursor-pointer items-center gap-2 rounded-md border px-2 py-1 text-sm"
            >
              <input
                type="checkbox"
                checked={selectedIds.includes(client.company_id)}
                onChange={() => toggleClient(client.company_id)}
              />
              {client.company_name}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
