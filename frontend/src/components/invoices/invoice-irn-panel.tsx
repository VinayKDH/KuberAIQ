"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useRegisterInvoiceIrn } from "@/features/invoices/hooks";
import type { Invoice } from "@/features/invoices/types";
import { COMPLIANCE_COPY } from "@/lib/constants";
import { formatDate } from "@/lib/format";

interface InvoiceIrnPanelProps {
  invoice: Invoice;
}

export function InvoiceIrnPanel({ invoice }: InvoiceIrnPanelProps) {
  const [irn, setIrn] = useState(invoice.irn ?? "");
  const [error, setError] = useState<string | null>(null);
  const registerIrn = useRegisterInvoiceIrn();
  const showPanel = !["DRAFT", "CANCELLED"].includes(invoice.status);

  if (!showPanel) return null;

  const hasIrn = Boolean(invoice.irn);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-base">E-invoice (IRN)</CardTitle>
        </div>
        <CardDescription>{COMPLIANCE_COPY.IRN_HINT}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {hasIrn ? (
          <div className="space-y-1">
            <Badge variant="default">IRN registered</Badge>
            <p className="break-all font-mono text-sm">{invoice.irn}</p>
            {invoice.irn_generated_at && (
              <p className="text-xs text-muted-foreground">
                Recorded {formatDate(invoice.irn_generated_at)}
              </p>
            )}
          </div>
        ) : (
          <>
            <p className="text-sm text-amber-700 dark:text-amber-300">
              {COMPLIANCE_COPY.IRN_REQUIRED}
            </p>
            <div className="space-y-2">
              <Label htmlFor="irn">{COMPLIANCE_COPY.IRN_LABEL}</Label>
              <Input
                id="irn"
                value={irn}
                onChange={(e) => setIrn(e.target.value.toUpperCase())}
                placeholder="64-character IRN from GST IRP"
                maxLength={64}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button
              className="w-full"
              disabled={registerIrn.isPending || irn.trim().length < 10}
              onClick={async () => {
                setError(null);
                try {
                  await registerIrn.mutateAsync({ id: invoice.id, irn: irn.trim() });
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Failed to save IRN");
                }
              }}
            >
              {registerIrn.isPending ? "Saving…" : COMPLIANCE_COPY.IRN_SAVE}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
