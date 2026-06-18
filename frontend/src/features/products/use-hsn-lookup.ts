import { useEffect, useState } from "react";
import { HSN_LOOKUP_DEBOUNCE_MS, HSN_LOOKUP_MIN_CHARS } from "@/lib/constants";
import { lookupHsnGst } from "./api";
import type { HsnLookupResult } from "./types";

/** Debounced GST catalogue lookup from a product / line-item name. */
export function useHsnLookupFromName(name: string, disabled = false) {
  const [result, setResult] = useState<HsnLookupResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (disabled) {
      setResult(null);
      setLoading(false);
      return;
    }

    const trimmed = name.trim();
    if (trimmed.length < HSN_LOOKUP_MIN_CHARS) {
      setResult(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    const timer = setTimeout(() => {
      lookupHsnGst({ name: trimmed })
        .then((response) => {
          if (cancelled) return;
          setResult(response.hsn_sac ? response : null);
        })
        .catch(() => {
          if (!cancelled) setResult(null);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }, HSN_LOOKUP_DEBOUNCE_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [name, disabled]);

  return { result, loading };
}
