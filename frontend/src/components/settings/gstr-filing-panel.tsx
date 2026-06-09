"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileJson } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient, downloadBlob } from "@/lib/api-client";
import { API_PATHS, GST_REPORT, GSTR_EXPORT, QUERY_KEYS } from "@/lib/constants";
import { formatINR } from "@/lib/format";

function monthBounds(): { from: string; to: string } {
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), 1);
  const to = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

export function GstrFilingPanel() {
  const defaults = useMemo(() => monthBounds(), []);
  const [fromDate, setFromDate] = useState(defaults.from);
  const [toDate, setToDate] = useState(defaults.to);
  const [showGstr1Json, setShowGstr1Json] = useState(false);
  const [showGstr3bJson, setShowGstr3bJson] = useState(false);

  const gstr1 = useQuery({
    queryKey: QUERY_KEYS.GSTR1_REPORT(fromDate, toDate),
    queryFn: () =>
      apiClient<{
        metadata: { disclaimer: string; invoice_count: number };
        b2b: unknown[];
        b2c_large: unknown[];
        b2c_small: unknown[];
        hsn_summary: unknown[];
      }>(API_PATHS.GSTR1_REPORT, { params: { from: fromDate, to: toDate } }),
    enabled: fromDate <= toDate,
  });

  const gstr3b = useQuery({
    queryKey: QUERY_KEYS.GSTR3B_REPORT(fromDate, toDate),
    queryFn: () =>
      apiClient<{
        metadata: { disclaimer: string; credit_note_count: number };
        outward_taxable: number | string;
        outward_cgst: number | string;
        outward_sgst: number | string;
        outward_igst: number | string;
        total_outward_tax: number | string;
      }>(API_PATHS.GSTR3B_REPORT, { params: { from: fromDate, to: toDate } }),
    enabled: fromDate <= toDate,
  });

  const rangeInvalid = fromDate > toDate;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileJson className="h-5 w-5 text-muted-foreground" />
          <CardTitle>GST filing exports</CardTitle>
        </div>
        <CardDescription>
          GSTR-1 and GSTR-3B summaries derived from issued invoices — verify on the GST portal before filing.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="gstr_from">{GST_REPORT.FROM_LABEL}</Label>
            <Input id="gstr_from" type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="gstr_to">{GST_REPORT.TO_LABEL}</Label>
            <Input id="gstr_to" type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </div>
        </div>

        {rangeInvalid && <p className="text-sm text-destructive">{GST_REPORT.INVALID_RANGE}</p>}

        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-3 rounded-lg border p-4">
            <h3 className="font-medium">{GSTR_EXPORT.GSTR1_TITLE}</h3>
            <p className="text-sm text-muted-foreground">{GSTR_EXPORT.GSTR1_DESCRIPTION}</p>
            {gstr1.isLoading && <Skeleton className="h-16 w-full" />}
            {gstr1.isError && <p className="text-sm text-destructive">{GSTR_EXPORT.LOAD_ERROR}</p>}
            {gstr1.data && (
              <>
                <p className="text-sm text-muted-foreground">{gstr1.data.metadata.disclaimer}</p>
                <p className="text-sm">B2B rows: {gstr1.data.b2b.length}</p>
                <p className="text-sm">HSN summary rows: {gstr1.data.hsn_summary.length}</p>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" onClick={() => setShowGstr1Json((v) => !v)}>
                    {showGstr1Json ? GSTR_EXPORT.HIDE_JSON : GSTR_EXPORT.VIEW_JSON}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      downloadBlob(API_PATHS.GSTR1_REPORT_CSV, `gstr1-${fromDate}_${toDate}.csv`, {
                        from: fromDate,
                        to: toDate,
                      })
                    }
                  >
                    <Download className="mr-2 h-4 w-4" />
                    {GSTR_EXPORT.DOWNLOAD_CSV}
                  </Button>
                </div>
                {showGstr1Json && (
                  <pre className="max-h-48 overflow-auto rounded-md border bg-muted/30 p-2 text-xs">
                    {JSON.stringify(gstr1.data, null, 2)}
                  </pre>
                )}
              </>
            )}
          </div>

          <div className="space-y-3 rounded-lg border p-4">
            <h3 className="font-medium">{GSTR_EXPORT.GSTR3B_TITLE}</h3>
            <p className="text-sm text-muted-foreground">{GSTR_EXPORT.GSTR3B_DESCRIPTION}</p>
            {gstr3b.isLoading && <Skeleton className="h-16 w-full" />}
            {gstr3b.isError && <p className="text-sm text-destructive">{GSTR_EXPORT.LOAD_ERROR}</p>}
            {gstr3b.data && (
              <>
                <p className="text-sm text-muted-foreground">{gstr3b.data.metadata.disclaimer}</p>
                <p className="text-sm">{GSTR_EXPORT.OUTWARD_TAXABLE}: {formatINR(gstr3b.data.outward_taxable)}</p>
                <p className="text-sm">{GSTR_EXPORT.TOTAL_OUTWARD_TAX}: {formatINR(gstr3b.data.total_outward_tax)}</p>
                <p className="text-sm">{GSTR_EXPORT.CREDIT_NOTES}: {gstr3b.data.metadata.credit_note_count}</p>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" onClick={() => setShowGstr3bJson((v) => !v)}>
                    {showGstr3bJson ? GSTR_EXPORT.HIDE_JSON : GSTR_EXPORT.VIEW_JSON}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      downloadBlob(API_PATHS.GSTR3B_REPORT_CSV, `gstr3b-${fromDate}_${toDate}.csv`, {
                        from: fromDate,
                        to: toDate,
                      })
                    }
                  >
                    <Download className="mr-2 h-4 w-4" />
                    {GSTR_EXPORT.DOWNLOAD_CSV}
                  </Button>
                </div>
                {showGstr3bJson && (
                  <pre className="max-h-48 overflow-auto rounded-md border bg-muted/30 p-2 text-xs">
                    {JSON.stringify(gstr3b.data, null, 2)}
                  </pre>
                )}
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
