"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileSpreadsheet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient, downloadBlob } from "@/lib/api-client";
import { API_PATHS, GST_REPORT, QUERY_KEYS } from "@/lib/constants";
import { formatINR } from "@/lib/format";

interface GstReport {
  from_date: string;
  to_date: string;
  invoice_count: number;
  taxable_amount: number | string;
  cgst_amount: number | string;
  sgst_amount: number | string;
  igst_amount: number | string;
  total_tax: number | string;
  grand_total: number | string;
}

function monthBounds(): { from: string; to: string } {
  const now = new Date();
  const from = new Date(now.getFullYear(), now.getMonth(), 1);
  const to = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return {
    from: from.toISOString().slice(0, 10),
    to: to.toISOString().slice(0, 10),
  };
}

export function GstReportPanel() {
  const defaults = useMemo(() => monthBounds(), []);
  const [fromDate, setFromDate] = useState(defaults.from);
  const [toDate, setToDate] = useState(defaults.to);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: QUERY_KEYS.GST_REPORT(fromDate, toDate),
    queryFn: () =>
      apiClient<GstReport>(API_PATHS.GST_REPORT, {
        params: { from: fromDate, to: toDate },
      }),
    enabled: Boolean(fromDate && toDate && fromDate <= toDate),
  });

  const handleDownload = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadBlob(API_PATHS.GST_REPORT_CSV, `gst-report-${fromDate}_${toDate}.csv`, {
        from: fromDate,
        to: toDate,
      });
    } catch (err) {
      setDownloadError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(false);
    }
  };

  const rangeInvalid = fromDate > toDate;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{GST_REPORT.TITLE}</CardTitle>
        </div>
        <CardDescription>{GST_REPORT.DESCRIPTION}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="gst-from">{GST_REPORT.FROM_LABEL}</Label>
            <Input
              id="gst-from"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="gst-to">{GST_REPORT.TO_LABEL}</Label>
            <Input
              id="gst-to"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
            />
          </div>
        </div>

        {rangeInvalid && (
          <p className="text-sm text-destructive">{GST_REPORT.INVALID_RANGE}</p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() => refetch()}
            disabled={rangeInvalid || isFetching}
          >
            {isFetching ? "Loading…" : GST_REPORT.REFRESH_LABEL}
          </Button>
          <Button
            onClick={handleDownload}
            disabled={rangeInvalid || downloading || !data}
          >
            <Download className="mr-2 h-4 w-4" />
            {downloading ? "Downloading…" : GST_REPORT.DOWNLOAD_LABEL}
          </Button>
        </div>

        {downloadError && <p className="text-sm text-destructive">{downloadError}</p>}

        {isError && (
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : GST_REPORT.LOAD_ERROR}
          </p>
        )}

        {isLoading && !data ? (
          <Skeleton className="h-32 w-full" />
        ) : data ? (
          <div className="grid gap-3 rounded-md border p-4 sm:grid-cols-2">
            <SummaryRow label={GST_REPORT.INVOICE_COUNT} value={String(data.invoice_count)} />
            <SummaryRow label={GST_REPORT.TAXABLE} value={formatINR(data.taxable_amount)} />
            <SummaryRow label={GST_REPORT.CGST} value={formatINR(data.cgst_amount)} />
            <SummaryRow label={GST_REPORT.SGST} value={formatINR(data.sgst_amount)} />
            <SummaryRow label={GST_REPORT.IGST} value={formatINR(data.igst_amount)} />
            <SummaryRow label={GST_REPORT.TOTAL_TAX} value={formatINR(data.total_tax)} />
            <SummaryRow
              label={GST_REPORT.GRAND_TOTAL}
              value={formatINR(data.grand_total)}
              emphasis
            />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function SummaryRow({
  label,
  value,
  emphasis,
}: {
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className={emphasis ? "font-semibold" : ""}>{value}</span>
    </div>
  );
}
