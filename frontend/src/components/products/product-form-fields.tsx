"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useHsnLookupFromName } from "@/features/products/use-hsn-lookup";
import { lookupHsnGst } from "@/features/products/api";
import type { Product } from "@/features/products/types";
import { GST_RATES, INVOICE_UNITS, PRODUCT_FORM } from "@/lib/constants";

export interface ProductFormValues {
  name: string;
  description: string;
  hsnSac: string;
  unit: string;
  defaultPrice: string;
  gstRate: string;
}

export function productToFormValues(product: Product): ProductFormValues {
  return {
    name: product.name,
    description: product.description ?? "",
    hsnSac: product.hsn_sac ?? "",
    unit: product.unit,
    defaultPrice: String(product.default_price),
    gstRate: String(product.gst_rate),
  };
}

export function productFormToPayload(values: ProductFormValues) {
  return {
    name: values.name.trim(),
    description: values.description.trim() || null,
    hsn_sac: values.hsnSac.trim() || null,
    unit: values.unit,
    default_price: Number(values.defaultPrice),
    gst_rate: Number(values.gstRate),
  };
}

export function validateProductForm(values: ProductFormValues): string | null {
  if (!values.name.trim()) return "Product name is required";
  if (!values.defaultPrice || Number(values.defaultPrice) < 0) return "Enter a valid price";
  return null;
}

interface ProductFormFieldsProps {
  values: ProductFormValues;
  onChange: (field: keyof ProductFormValues, value: string) => void;
}

export function ProductFormFields({ values, onChange }: ProductFormFieldsProps) {
  const [gstAutoFilled, setGstAutoFilled] = useState(false);
  const [hsnManuallyEdited, setHsnManuallyEdited] = useState(false);
  const [matchedLabel, setMatchedLabel] = useState<string | null>(null);
  const { result, loading } = useHsnLookupFromName(values.name, hsnManuallyEdited);

  useEffect(() => {
    if (hsnManuallyEdited || !result?.hsn_sac) {
      if (!result?.hsn_sac) setMatchedLabel(null);
      return;
    }
    setMatchedLabel(result.matched_label ?? null);
    onChange("hsnSac", result.hsn_sac);
    if (result.gst_rate != null && result.gst_rate !== "") {
      onChange("gstRate", String(result.gst_rate));
      setGstAutoFilled(true);
    }
  }, [result, hsnManuallyEdited, onChange]);

  const handleHsnBlur = async () => {
    const hsn = values.hsnSac.trim();
    if (!hsn) return;
    try {
      const lookupResult = await lookupHsnGst({ hsn_sac: hsn });
      if (lookupResult.gst_rate != null && lookupResult.gst_rate !== "") {
        onChange("gstRate", String(lookupResult.gst_rate));
        setGstAutoFilled(true);
      }
    } catch {
      /* lookup is best-effort */
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="product-name">{PRODUCT_FORM.NAME}</Label>
        <Input
          id="product-name"
          value={values.name}
          onChange={(e) => {
            setHsnManuallyEdited(false);
            setGstAutoFilled(false);
            onChange("name", e.target.value);
          }}
          placeholder="OPC 53 Grade Cement"
          required
        />
        {loading && (
          <p className="text-xs text-muted-foreground">Matching GST catalogue…</p>
        )}
        {!loading && matchedLabel && (
          <p className="text-xs text-muted-foreground">
            {PRODUCT_FORM.GST_MATCHED} {matchedLabel}
          </p>
        )}
      </div>
      <div className="space-y-2">
        <Label htmlFor="product-description">{PRODUCT_FORM.DESCRIPTION_FIELD}</Label>
        <Textarea
          id="product-description"
          value={values.description}
          onChange={(e) => onChange("description", e.target.value)}
          rows={2}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="product-hsn">{PRODUCT_FORM.HSN_SAC}</Label>
          <Input
            id="product-hsn"
            value={values.hsnSac}
            onChange={(e) => {
              setHsnManuallyEdited(true);
              setGstAutoFilled(false);
              setMatchedLabel(null);
              onChange("hsnSac", e.target.value);
            }}
            onBlur={handleHsnBlur}
            placeholder="2523"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="product-unit">{PRODUCT_FORM.UNIT}</Label>
          <Select
            id="product-unit"
            options={INVOICE_UNITS.map((u) => ({ value: u, label: u }))}
            value={values.unit}
            onValueChange={(v) => onChange("unit", v)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="product-price">{PRODUCT_FORM.DEFAULT_PRICE}</Label>
          <Input
            id="product-price"
            type="number"
            min="0"
            step="0.01"
            value={values.defaultPrice}
            onChange={(e) => onChange("defaultPrice", e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="product-gst">{PRODUCT_FORM.GST_RATE}</Label>
          <Select
            id="product-gst"
            options={GST_RATES.map((r) => ({ value: String(r), label: `${r}%` }))}
            value={values.gstRate}
            onValueChange={(v) => {
              setGstAutoFilled(false);
              onChange("gstRate", v);
            }}
          />
          {gstAutoFilled && (
            <p className="text-xs text-muted-foreground">{PRODUCT_FORM.GST_AUTO_FILLED}</p>
          )}
        </div>
      </div>
    </div>
  );
}
