"use client";

import { useState } from "react";
import { Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateCustomer } from "@/features/customers/hooks";
import { MSME_QUICK_START_COPY, MSME_STARTER_CUSTOMERS } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import {
  getMsmeSegmentLabel,
  getStoredMsmeSegment,
  isStarterCustomersImported,
  markStarterCustomersImported,
} from "@/lib/msme-segment";

type StarterCustomersBannerProps = {
  customerCount: number;
};

export function StarterCustomersBanner({ customerCount }: StarterCustomersBannerProps) {
  const lang = getPreferredLanguage();
  const segmentId = getStoredMsmeSegment();
  const starters = MSME_STARTER_CUSTOMERS[segmentId];
  const createCustomer = useCreateCustomer();
  const [imported, setImported] = useState(() => isStarterCustomersImported(segmentId));
  const [error, setError] = useState<string | null>(null);

  if (imported || customerCount > 0) return null;

  const importLabel = MSME_QUICK_START_COPY.IMPORT_CUSTOMERS_BUTTON[lang].replace(
    "{count}",
    String(starters.length),
  );

  const handleImport = async () => {
    setError(null);
    try {
      for (const item of starters) {
        await createCustomer.mutateAsync({
          name: item.name,
          phone: item.phone,
          gstin: item.gstin,
        });
      }
      markStarterCustomersImported(segmentId);
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
            <Users className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base">
              {MSME_QUICK_START_COPY.IMPORT_CUSTOMERS_TITLE[lang]}
            </CardTitle>
            <CardDescription>
              {getMsmeSegmentLabel(segmentId, lang)} ·{" "}
              {MSME_QUICK_START_COPY.IMPORT_CUSTOMERS_DESC[lang]}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <ul className="grid gap-1 text-sm text-muted-foreground sm:grid-cols-2">
          {starters.map((item) => (
            <li key={item.phone} className="truncate">
              · {item.name} ({item.phone})
            </li>
          ))}
        </ul>
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button onClick={handleImport} disabled={createCustomer.isPending}>
          {createCustomer.isPending ? MSME_QUICK_START_COPY.IMPORTING[lang] : importLabel}
        </Button>
      </CardContent>
    </Card>
  );
}
