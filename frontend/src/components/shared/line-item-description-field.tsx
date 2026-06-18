"use client";

import { useEffect, useRef, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useHsnLookupFromName } from "@/features/products/use-hsn-lookup";
import { PRODUCT_FORM } from "@/lib/constants";

interface LineItemDescriptionFieldProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  onTaxMatch?: (match: { hsn_sac: string; gst_rate: number; matched_label?: string | null }) => void;
  placeholder?: string;
}

/** Description text box with debounced GST catalogue matching for HSN/GST autofill. */
export function LineItemDescriptionField({
  value,
  onChange,
  disabled = false,
  onTaxMatch,
  placeholder = "OPC 53 Grade Cement",
}: LineItemDescriptionFieldProps) {
  const [matchedLabel, setMatchedLabel] = useState<string | null>(null);
  const { result, loading } = useHsnLookupFromName(value, disabled);
  const onTaxMatchRef = useRef(onTaxMatch);
  onTaxMatchRef.current = onTaxMatch;

  useEffect(() => {
    if (!result?.hsn_sac || result.gst_rate == null) {
      setMatchedLabel(null);
      return;
    }
    setMatchedLabel(result.matched_label ?? null);
    onTaxMatchRef.current?.({
      hsn_sac: result.hsn_sac,
      gst_rate: Number(result.gst_rate),
      matched_label: result.matched_label,
    });
  }, [result]);

  return (
    <div className="space-y-2">
      <Label>Description</Label>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
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
  );
}
