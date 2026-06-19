"use client";

import { useState } from "react";
import { PackagePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateProduct } from "@/features/products/hooks";
import { MSME_QUICK_START_COPY, MSME_STARTER_PRODUCTS } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import {
  getMsmeSegmentLabel,
  getStoredMsmeSegment,
  isStarterProductsImported,
  markStarterProductsImported,
} from "@/lib/msme-segment";

type StarterProductsBannerProps = {
  productCount: number;
};

export function StarterProductsBanner({ productCount }: StarterProductsBannerProps) {
  const lang = getPreferredLanguage();
  const segmentId = getStoredMsmeSegment();
  const starters = MSME_STARTER_PRODUCTS[segmentId];
  const createProduct = useCreateProduct();
  const [imported, setImported] = useState(() => isStarterProductsImported(segmentId));
  const [error, setError] = useState<string | null>(null);

  if (imported || productCount > 0) return null;

  const importLabel = MSME_QUICK_START_COPY.IMPORT_BUTTON[lang].replace(
    "{count}",
    String(starters.length),
  );

  const handleImport = async () => {
    setError(null);
    try {
      for (const item of starters) {
        await createProduct.mutateAsync({
          name: item.name,
          hsn_sac: item.hsn_sac,
          unit: item.unit,
          default_price: item.default_price,
          gst_rate: item.gst_rate,
        });
      }
      markStarterProductsImported(segmentId);
      setImported(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    }
  };

  return (
    <Card className="border-dashed border-primary/30 bg-primary/5">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <PackagePlus className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base">{MSME_QUICK_START_COPY.IMPORT_TITLE[lang]}</CardTitle>
            <CardDescription>
              {getMsmeSegmentLabel(segmentId, lang)} · {MSME_QUICK_START_COPY.IMPORT_DESC[lang]}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <ul className="grid gap-1 text-sm text-muted-foreground sm:grid-cols-2">
          {starters.map((item) => (
            <li key={item.name} className="truncate">
              · {item.name} ({item.hsn_sac})
            </li>
          ))}
        </ul>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button onClick={handleImport} disabled={createProduct.isPending}>
          {createProduct.isPending ? MSME_QUICK_START_COPY.IMPORTING[lang] : importLabel}
        </Button>
      </CardContent>
    </Card>
  );
}
