"use client";

import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCaBulkGstr1, useCaBulkGstr3b } from "@/features/ca/hooks";
import { CA_COPY } from "@/lib/constants";
import { financialYearStartIso, todayIso } from "@/lib/format";
import type { CaDashboardClient } from "@/features/ca/types";

type GstrReportType = "gstr1" | "gstr3b";

interface CaBulkGstrPanelProps {
  clients: CaDashboardClient[];
}

export function CaBulkGstrPanel({ clients }: CaBulkGstrPanelProps) {
  const [reportType, setReportType] = useState<GstrReportType>("gstr1");
  const [fromDate, setFromDate] = useState(financialYearStartIso);
  const [toDate, setToDate] = useState(todayIso);
  const [selected, setSelected] = useState<Set<string>>(() => new Set(clients.map((c) => c.company_id)));
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bulkGstr1 = useCaBulkGstr1();
  const bulkGstr3b = useCaBulkGstr3b();
  const isPending = bulkGstr1.isPending || bulkGstr3b.isPending;

  const allSelected = useMemo(
    () => clients.length > 0 && selected.size === clients.length,
    [clients.length, selected.size],
  );

  const toggleClient = (companyId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(companyId)) next.delete(companyId);
      else next.add(companyId);
      return next;
    });
  };

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(clients.map((client) => client.company_id)));
    }
  };

  const handleExport = async () => {
    setMessage(null);
    setError(null);
    const companyIds = Array.from(selected);
    if (!companyIds.length) {
      setError(CA_COPY.BULK_GSTR_EMPTY);
      return;
    }
    try {
      const params = { from: fromDate, to: toDate, companyIds };
      const data =
        reportType === "gstr1"
          ? await bulkGstr1.mutateAsync(params)
          : await bulkGstr3b.mutateAsync(params);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${reportType}-bulk-${fromDate}-to-${toDate}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      setMessage(CA_COPY.BULK_GSTR_SUCCESS);
    } catch (err) {
      setError(err instanceof Error ? err.message : CA_COPY.BULK_GSTR_ERROR);
    }
  };

  if (!clients.length) return null;

  const title = reportType === "gstr1" ? CA_COPY.BULK_GSTR_TITLE : CA_COPY.BULK_GSTR3B_TITLE;
  const desc = reportType === "gstr1" ? CA_COPY.BULK_GSTR_DESC : CA_COPY.BULK_GSTR3B_DESC;
  const exportLabel =
    reportType === "gstr1" ? CA_COPY.BULK_GSTR_EXPORT : CA_COPY.BULK_GSTR3B_EXPORT;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{desc}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={reportType === "gstr1" ? "default" : "outline"}
            onClick={() => setReportType("gstr1")}
          >
            {CA_COPY.BULK_GSTR_TAB_GSTR1}
          </Button>
          <Button
            type="button"
            size="sm"
            variant={reportType === "gstr3b" ? "default" : "outline"}
            onClick={() => setReportType("gstr3b")}
          >
            {CA_COPY.BULK_GSTR_TAB_GSTR3B}
          </Button>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="space-y-1">
            <Label htmlFor="gstr-from">From</Label>
            <Input
              id="gstr-from"
              type="date"
              value={fromDate}
              max={toDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="gstr-to">To</Label>
            <Input
              id="gstr-to"
              type="date"
              value={toDate}
              min={fromDate}
              max={todayIso()}
              onChange={(e) => setToDate(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>{CA_COPY.BULK_GSTR_SELECT}</Label>
            <Button type="button" variant="ghost" size="sm" onClick={toggleAll}>
              {allSelected ? "Clear all" : "Select all"}
            </Button>
          </div>
          <div className="max-h-40 space-y-2 overflow-y-auto rounded-md border p-3">
            {clients.map((client) => (
              <label key={client.company_id} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selected.has(client.company_id)}
                  onChange={() => toggleClient(client.company_id)}
                />
                <span>{client.company_name}</span>
              </label>
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}
        {message && <p className="text-sm text-emerald-600">{message}</p>}

        <Button onClick={handleExport} disabled={isPending}>
          <Download className="mr-2 h-4 w-4" />
          {isPending ? CA_COPY.BULK_GSTR_EXPORTING : exportLabel}
        </Button>
      </CardContent>
    </Card>
  );
}
