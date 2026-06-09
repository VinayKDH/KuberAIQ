"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useCustomers } from "@/features/customers/hooks";
import { useProducts } from "@/features/products/hooks";
import type { CreateQuotationInput, QuotationLineInput } from "@/features/quotations/types";
import {
  DEFAULT_DUE_DAYS,
  GST_RATES,
  INVOICE_LINE_MODE,
  INVOICE_UNITS,
} from "@/lib/constants";
import { addDaysIso, todayIso } from "@/lib/format";

const emptyLine = (): QuotationLineInput => ({
  description: "",
  quantity: 1,
  unit_price: 0,
  gst_rate: 18,
  unit: "NOS",
});

interface QuotationFormProps {
  onSubmit: (input: CreateQuotationInput) => Promise<void>;
  isSubmitting?: boolean;
}

export function QuotationForm({ onSubmit, isSubmitting }: QuotationFormProps) {
  const { data: customersData } = useCustomers({ page: 1, page_size: 100 });
  const { data: productsData } = useProducts({ page: 1, page_size: 100, active_only: true });
  const [customerId, setCustomerId] = useState("");
  const [issueDate, setIssueDate] = useState(todayIso());
  const [validUntil, setValidUntil] = useState(addDaysIso(DEFAULT_DUE_DAYS));
  const [lines, setLines] = useState<QuotationLineInput[]>([emptyLine()]);
  const [error, setError] = useState<string | null>(null);

  const customerOptions =
    customersData?.items.map((c) => ({ value: c.id, label: `${c.name} (${c.phone})` })) ?? [];

  const productOptions = [
    { value: "", label: INVOICE_LINE_MODE.CUSTOM },
    ...(productsData?.items.map((p) => ({
      value: p.id,
      label: `${p.name} — ${p.default_price}`,
    })) ?? []),
  ];

  const updateLine = (index: number, patch: Partial<QuotationLineInput>) => {
    setLines((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  };

  const applyProduct = (index: number, productId: string) => {
    if (!productId) {
      updateLine(index, { product_id: undefined });
      return;
    }
    const product = productsData?.items.find((p) => p.id === productId);
    if (!product) return;
    updateLine(index, {
      product_id: product.id,
      description: product.name,
      unit_price: Number(product.default_price),
      gst_rate: Number(product.gst_rate),
      hsn_sac: product.hsn_sac ?? undefined,
      unit: product.unit,
    });
  };

  const addLine = () => setLines((prev) => [...prev, emptyLine()]);

  const removeLine = (index: number) => {
    setLines((prev) => (prev.length === 1 ? prev : prev.filter((_, i) => i !== index)));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!customerId) {
      setError("Select a customer");
      return;
    }
    if (lines.some((l) => !l.description.trim() || l.quantity <= 0)) {
      setError("Each line needs a description and quantity greater than zero");
      return;
    }

    await onSubmit({
      customer_id: customerId,
      issue_date: issueDate,
      valid_until: validUntil,
      items: lines.map((line) => ({
        description: line.description.trim(),
        quantity: Number(line.quantity),
        unit_price: Number(line.unit_price),
        gst_rate: Number(line.gst_rate),
        hsn_sac: line.hsn_sac,
        unit: line.unit ?? "NOS",
        product_id: line.product_id,
      })),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quotation details</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="customer">Customer</Label>
            <Select
              id="customer"
              options={customerOptions}
              placeholder="Select customer"
              value={customerId}
              onValueChange={setCustomerId}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="issue_date">Issue date</Label>
            <Input
              id="issue_date"
              type="date"
              value={issueDate}
              onChange={(e) => setIssueDate(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="valid_until">Valid until</Label>
            <Input
              id="valid_until"
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
              required
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Line items</CardTitle>
          <Button type="button" variant="outline" size="sm" onClick={addLine}>
            <Plus className="mr-1 h-4 w-4" />
            Add line
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {lines.map((line, index) => (
            <div key={index} className="grid gap-3 rounded-lg border p-4 md:grid-cols-6">
              <div className="space-y-2 md:col-span-2">
                <Label>Product</Label>
                <Select
                  options={productOptions}
                  value={line.product_id ?? ""}
                  onValueChange={(v) => applyProduct(index, v)}
                />
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label>Description</Label>
                <Input
                  value={line.description}
                  onChange={(e) => updateLine(index, { description: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Qty</Label>
                <Input
                  type="number"
                  min="0.001"
                  step="0.001"
                  value={line.quantity}
                  onChange={(e) => updateLine(index, { quantity: Number(e.target.value) })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Unit price (₹)</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={line.unit_price}
                  onChange={(e) => updateLine(index, { unit_price: Number(e.target.value) })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>GST %</Label>
                <Select
                  options={GST_RATES.map((r) => ({ value: String(r), label: `${r}%` }))}
                  value={String(line.gst_rate)}
                  onValueChange={(v) => updateLine(index, { gst_rate: Number(v) })}
                />
              </div>
              <div className="space-y-2">
                <Label>Unit</Label>
                <Select
                  options={INVOICE_UNITS.map((u) => ({ value: u, label: u }))}
                  value={line.unit ?? "NOS"}
                  onValueChange={(v) => updateLine(index, { unit: v })}
                />
              </div>
              <div className="flex items-end md:col-span-6">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeLine(index)}
                  disabled={lines.length === 1}
                >
                  <Trash2 className="mr-1 h-4 w-4" />
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <div className="flex justify-end">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Save quotation"}
        </Button>
      </div>
    </form>
  );
}
