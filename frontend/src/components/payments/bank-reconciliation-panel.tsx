"use client";

import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { API_PATHS, PAYMENT_COPY } from "@/lib/constants";
import { formatINR } from "@/lib/format";

interface CsvMatchRow {
  reference: string;
  amount: number;
  paid_on: string;
  matched_invoice_id: string | null;
  matched_invoice_number: string | null;
  match_confidence: string;
}

export function BankReconciliationPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [rows, setRows] = useState<CsvMatchRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/api/v1${API_PATHS.PAYMENTS_IMPORT_CSV}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("kuberaiq_access_token") ?? ""}`,
        },
        body: form,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = (await res.json()) as { items: CsvMatchRow[] };
      setRows(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }

  async function applyMatches() {
    const matched = rows.filter((r) => r.matched_invoice_id);
    if (!matched.length) return;
    setApplying(true);
    setError(null);
    try {
      await apiClient(API_PATHS.PAYMENTS_IMPORT_CSV_APPLY, {
        method: "POST",
        body: {
          items: matched.map((r) => ({
            invoice_id: r.matched_invoice_id,
            amount: r.amount,
            paid_on: r.paid_on,
            method: "BANK_TRANSFER",
            reference: r.reference || undefined,
          })),
        },
      });
      setRows([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Apply failed");
    } finally {
      setApplying(false);
    }
  }

  const matchable = rows.filter((r) => r.matched_invoice_id);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{PAYMENT_COPY.CSV_IMPORT_TITLE}</CardTitle>
        <CardDescription>{PAYMENT_COPY.CSV_IMPORT_HINT}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleUpload(file);
          }}
        />
        <Button variant="outline" disabled={loading} onClick={() => inputRef.current?.click()}>
          <Upload className="mr-2 h-4 w-4" />
          Upload bank CSV
        </Button>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {rows.length > 0 && (
          <>
            <ul className="max-h-48 space-y-1 overflow-y-auto text-sm">
              {rows.map((row, i) => (
                <li key={i} className="flex justify-between gap-2 border-b py-1">
                  <span>
                    {row.reference || "—"} → {row.matched_invoice_number ?? "no match"}
                  </span>
                  <span>{formatINR(row.amount)}</span>
                </li>
              ))}
            </ul>
            <Button disabled={applying || !matchable.length} onClick={() => void applyMatches()}>
              {applying ? PAYMENT_COPY.CSV_APPLYING : `${PAYMENT_COPY.CSV_APPLY} (${matchable.length})`}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
