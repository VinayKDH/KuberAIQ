"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, Download } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { downloadCustomerStatement } from "@/features/customers/api";
import { useCustomerHistory, useCustomerLedger } from "@/features/customers/hooks";
import { EditCustomerDialog } from "@/components/customers/edit-customer-dialog";
import { AGING_BUCKET_LABELS, CUSTOMER_STATEMENT, ROUTES } from "@/lib/constants";
import { formatDate, formatINR, formatPhone, maskGstin } from "@/lib/format";

export default function CustomerDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const { data, isLoading, isError, error } = useCustomerHistory(id);
  const { data: ledger } = useCustomerLedger(id);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <p className="text-destructive">
        {error instanceof Error ? error.message : "Customer not found"}
      </p>
    );
  }

  const { customer } = data;

  return (
    <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
        <Link href={ROUTES.CUSTOMERS}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div className="flex-1">
          <h2 className="text-2xl font-bold tracking-tight">{customer.name}</h2>
          <p className="text-muted-foreground">
            {formatPhone(customer.phone)}
            {customer.email ? ` · ${customer.email}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={downloading}
            onClick={async () => {
              setDownloading(true);
              setDownloadError(null);
              try {
                await downloadCustomerStatement(id, `${customer.name}-statement.pdf`);
              } catch (err) {
                setDownloadError(err instanceof Error ? err.message : "Download failed");
              } finally {
                setDownloading(false);
              }
            }}
          >
            <Download className="mr-2 h-4 w-4" />
            {downloading ? CUSTOMER_STATEMENT.DOWNLOADING : CUSTOMER_STATEMENT.DOWNLOAD_LABEL}
          </Button>
          <EditCustomerDialog customer={customer} />
        </div>
      </div>

      {downloadError && <p className="text-sm text-destructive">{downloadError}</p>}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total billed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatINR(data.total_billed)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total paid
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{formatINR(data.total_paid)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Outstanding
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-destructive">
              {formatINR(data.outstanding)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Customer details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 text-sm md:grid-cols-2">
          <div>
            <span className="text-muted-foreground">GSTIN: </span>
            {customer.gstin ? maskGstin(customer.gstin) : "—"}
          </div>
          <div>
            <span className="text-muted-foreground">State: </span>
            {customer.state_code ?? "—"}
          </div>
          <div className="md:col-span-2">
            <span className="text-muted-foreground">Address: </span>
            {customer.billing_address ?? "—"}
          </div>
          {customer.created_at && (
            <div>
              <span className="text-muted-foreground">Added: </span>
              {formatDate(customer.created_at)}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Aging breakdown</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {Object.entries(data.aging).map(([bucket, amount]) => (
            <Badge key={bucket} variant="outline" className="px-3 py-1">
              {AGING_BUCKET_LABELS[bucket] ?? bucket}: {formatINR(amount)}
            </Badge>
          ))}
          {Object.keys(data.aging).length === 0 && (
            <p className="text-sm text-muted-foreground">No outstanding receivables</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Payment ledger</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {ledger?.entries?.length ? (
            ledger.entries.map((entry) => (
              <div key={entry.id} className="flex items-center justify-between rounded border p-2">
                <div>
                  <p className="font-medium">
                    {entry.kind} · {entry.reference ?? entry.id.slice(0, 8)}
                  </p>
                  <p className="text-muted-foreground">{formatDate(entry.date)}</p>
                </div>
                <div className="text-right">
                  <p>Dr {formatINR(entry.debit)}</p>
                  <p>Cr {formatINR(entry.credit)}</p>
                  <p className="text-muted-foreground">Bal {formatINR(entry.balance)}</p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No ledger entries yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
