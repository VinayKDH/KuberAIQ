"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useConvertQuotation,
  useDownloadQuotationPdf,
  useQuotation,
  useSendQuotation,
} from "@/features/quotations/hooks";
import {
  QUOTATION_COPY,
  QUOTATION_STATUS_LABELS,
  QUOTATION_STATUS_VARIANTS,
  ROUTES,
} from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";

export default function QuotationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = String(params.id);
  const { data: quotation, isLoading, isError, error } = useQuotation(id);
  const sendQuotation = useSendQuotation();
  const convertQuotation = useConvertQuotation();
  const downloadPdf = useDownloadQuotationPdf();
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (isError || !quotation) {
    return (
      <p className="text-destructive">
        {error instanceof Error ? error.message : "Quotation not found"}
      </p>
    );
  }

  const canSend = quotation.status === "DRAFT";
  const canConvert = quotation.status === "SENT";
  const canDownload = quotation.status !== "DRAFT";

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <Link href={ROUTES.QUOTATIONS}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-2xl font-bold tracking-tight">
                {quotation.quotation_number ?? "Draft quotation"}
              </h2>
              <Badge variant={QUOTATION_STATUS_VARIANTS[quotation.status] ?? "secondary"}>
                {QUOTATION_STATUS_LABELS[quotation.status] ?? quotation.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {quotation.customer?.name ?? "Customer"} · Issued {formatDate(quotation.issue_date)} ·{" "}
              {QUOTATION_COPY.VALID_UNTIL} {formatDate(quotation.valid_until)}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {canDownload && (
            <Button
              variant="outline"
              disabled={downloadPdf.isPending}
              onClick={async () => {
                setActionError(null);
                try {
                  await downloadPdf.mutateAsync({
                    id,
                    filename: `${quotation.quotation_number ?? id}.pdf`,
                  });
                } catch (err) {
                  setActionError(err instanceof Error ? err.message : "PDF download failed");
                }
              }}
            >
              <Download className="mr-1 h-4 w-4" />
              Download PDF
            </Button>
          )}
          {canSend && (
            <Button
              disabled={sendQuotation.isPending}
              onClick={async () => {
                setActionError(null);
                try {
                  await sendQuotation.mutateAsync(id);
                } catch (err) {
                  setActionError(err instanceof Error ? err.message : "Failed to send quotation");
                }
              }}
            >
              {QUOTATION_COPY.SEND}
            </Button>
          )}
          {canConvert && (
            <Button
              disabled={convertQuotation.isPending}
              onClick={async () => {
                setActionError(null);
                try {
                  const result = await convertQuotation.mutateAsync(id);
                  router.push(ROUTES.INVOICE_DETAIL(result.invoice_id));
                } catch (err) {
                  setActionError(err instanceof Error ? err.message : "Conversion failed");
                }
              }}
            >
              {QUOTATION_COPY.CONVERT}
            </Button>
          )}
          {quotation.converted_invoice_id && (
            <Link href={ROUTES.INVOICE_DETAIL(quotation.converted_invoice_id)}>
              <Button variant="outline">{QUOTATION_COPY.CONVERTED_LINK}</Button>
            </Link>
          )}
        </div>
      </div>

      {actionError && (
        <p className="text-sm text-destructive" role="alert">
          {actionError}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Line items</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead>Rate</TableHead>
                  <TableHead>GST</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {quotation.items.map((item) => (
                  <TableRow key={item.line_no}>
                    <TableCell>{item.line_no}</TableCell>
                    <TableCell>{item.description}</TableCell>
                    <TableCell>
                      {item.quantity} {item.unit}
                    </TableCell>
                    <TableCell>{formatINR(item.unit_price)}</TableCell>
                    <TableCell>{item.gst_rate}%</TableCell>
                    <TableCell className="text-right">{formatINR(item.line_total)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Totals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Taxable</span>
              <span>{formatINR(quotation.taxable_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total tax</span>
              <span>{formatINR(quotation.total_tax)}</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span>Grand total</span>
              <span>{formatINR(quotation.grand_total)}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
