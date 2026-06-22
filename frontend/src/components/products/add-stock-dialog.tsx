"use client";

import { useState } from "react";
import { PackagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useAdjustProductStock } from "@/features/products/hooks";
import type { Product } from "@/features/products/types";
import { INVENTORY_COPY, STOCK_ADJUSTMENT_REASONS } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import { formatQty } from "@/lib/format";

interface AddStockDialogProps {
  product: Product;
}

export function AddStockDialog({ product }: AddStockDialogProps) {
  const lang = getPreferredLanguage();
  const copy = INVENTORY_COPY;
  const [open, setOpen] = useState(false);
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState<string>(STOCK_ADJUSTMENT_REASONS[0]);
  const [error, setError] = useState<string | null>(null);
  const adjustStock = useAdjustProductStock();

  const reset = () => {
    setQuantity("");
    setReason(STOCK_ADJUSTMENT_REASONS[0]);
    setError(null);
  };

  const handleSubmit = async () => {
    setError(null);
    const delta = Number(quantity);
    if (!quantity || !Number.isFinite(delta) || delta <= 0) {
      setError("Enter a valid quantity to add");
      return;
    }
    try {
      await adjustStock.mutateAsync({
        id: product.id,
        input: { delta, reason },
      });
      setOpen(false);
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update stock");
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (!value) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <PackagePlus className="mr-2 h-4 w-4" />
          {copy.ADD_STOCK[lang]}
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>{copy.ADD_STOCK_TITLE[lang]}</DialogTitle>
          <DialogDescription>{copy.ADD_STOCK_DESCRIPTION[lang]}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {product.name} · {copy.CURRENT_STOCK[lang]}: {formatQty(product.stock_qty ?? 0)}{" "}
            {product.unit}
          </p>
          <div className="space-y-2">
            <Label htmlFor={`stock-qty-${product.id}`}>{copy.QUANTITY_TO_ADD[lang]}</Label>
            <Input
              id={`stock-qty-${product.id}`}
              type="number"
              min="0.001"
              step="any"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="10"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor={`stock-reason-${product.id}`}>{copy.REASON[lang]}</Label>
            <Select
              id={`stock-reason-${product.id}`}
              options={STOCK_ADJUSTMENT_REASONS.map((r) => ({ value: r, label: r }))}
              value={reason}
              onValueChange={setReason}
            />
          </div>
        </div>

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <Button className="w-full" disabled={adjustStock.isPending} onClick={handleSubmit}>
          {adjustStock.isPending ? "Saving…" : copy.SAVE_STOCK[lang]}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
