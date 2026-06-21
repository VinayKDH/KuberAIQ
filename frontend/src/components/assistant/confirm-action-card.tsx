"use client";

import { Button } from "@/components/ui/button";
import { formatINR } from "@/lib/format";
import type { PendingAction } from "@/features/assistant/types";

interface ConfirmActionCardProps {
  pendingAction: PendingAction;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

function renderPreview(pendingAction: PendingAction): string {
  const preview = pendingAction.preview;
  if (pendingAction.type === "create_invoice") {
    const customer = preview.customer_name ?? "Customer";
    const items = Array.isArray(preview.items) ? preview.items : [];
    const first = items[0] as Record<string, unknown> | undefined;
    const qty = first?.quantity ?? "—";
    const price = first?.unit_price ?? "—";
    const gst = first?.gst_rate ?? "—";
    const itemSuffix = items.length > 1 ? ` · +${items.length - 1} more` : "";
    return `${customer} · ${qty} @ ₹${price} · ${gst}% GST${itemSuffix} · due ${preview.due_date ?? "—"}`;
  }
  if (pendingAction.type === "create_customer_and_invoice") {
    const customer = preview.customer as Record<string, unknown> | undefined;
    const invoice = preview.invoice as Record<string, unknown> | undefined;
    const items = Array.isArray(invoice?.items) ? invoice.items : [];
    const first = items[0] as Record<string, unknown> | undefined;
    const name = customer?.name ?? "Customer";
    const phone = customer?.phone ?? "—";
    const qty = first?.quantity ?? "—";
    const desc = first?.description ?? "Item";
    const itemSuffix = items.length > 1 ? ` · +${items.length - 1} more` : "";
    return `${name} · ${phone} · ${qty} ${desc}${itemSuffix}`;
  }
  if (pendingAction.type === "create_customer") {
    return `${preview.name ?? "Customer"} · ${preview.phone ?? "—"}`;
  }
  if (pendingAction.type === "bulk_send_reminders") {
    return `${preview.count ?? 0} invoices · ${formatINR(Number(preview.total_outstanding ?? 0))} outstanding`;
  }
  return JSON.stringify(preview);
}

export function ConfirmActionCard({
  pendingAction,
  onConfirm,
  onCancel,
  loading,
}: ConfirmActionCardProps) {
  return (
    <div className="mt-3 rounded-md border border-primary/30 bg-background p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Confirm action
      </p>
      <p className="mt-1 text-sm">{renderPreview(pendingAction)}</p>
      <div className="mt-3 flex gap-2">
        <Button size="sm" onClick={onConfirm} disabled={loading}>
          Confirm
        </Button>
        <Button size="sm" variant="outline" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
