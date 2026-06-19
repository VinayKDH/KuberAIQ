"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, FileText, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useMsmeSegment } from "@/features/company/hooks";
import { createCustomer } from "@/features/customers/api";
import { useCreateInvoice } from "@/features/invoices/hooks";
import {
  ASSISTANT_QUERY_PARAM,
  MSME_QUICK_START_ACTIONS,
  MSME_QUICK_START_COPY,
  MSME_STARTER_CUSTOMERS,
  MSME_STARTER_PRODUCTS,
  ROUTES,
} from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import {
  dismissQuickStart,
  getMsmeSegmentLabel,
  isQuickStartDismissed,
  isSampleInvoiceCreated,
  markSampleInvoiceCreated,
} from "@/lib/msme-segment";
import { todayIso } from "@/lib/format";

export function MsmeQuickStartCard() {
  const lang = getPreferredLanguage();
  const segmentId = useMsmeSegment();
  const router = useRouter();
  const createInvoice = useCreateInvoice();
  const [visible, setVisible] = useState(false);
  const [sampleDone, setSampleDone] = useState(() => isSampleInvoiceCreated());
  const [samplePending, setSamplePending] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);

  useEffect(() => {
    if (isQuickStartDismissed()) return;
    setVisible(true);
  }, []);

  if (!visible) return null;

  const actions = MSME_QUICK_START_ACTIONS[segmentId];

  const handleDismiss = () => {
    dismissQuickStart();
    setVisible(false);
  };

  const handleSampleInvoice = async () => {
    setSampleError(null);
    setSamplePending(true);
    try {
      const starterCustomer = MSME_STARTER_CUSTOMERS[segmentId][0];
      const starterProduct = MSME_STARTER_PRODUCTS[segmentId][0];
      const customer = await createCustomer({
        name: starterCustomer.name,
        phone: starterCustomer.phone,
        gstin: starterCustomer.gstin,
      });
      const issueDate = todayIso();
      const due = new Date();
      due.setDate(due.getDate() + 15);
      const invoice = await createInvoice.mutateAsync({
        customer_id: customer.id,
        issue_date: issueDate,
        due_date: due.toISOString().slice(0, 10),
        status: "DRAFT",
        items: [
          {
            description: starterProduct.name,
            quantity: 1,
            unit: starterProduct.unit,
            unit_price: starterProduct.default_price,
            gst_rate: starterProduct.gst_rate,
            hsn_sac: starterProduct.hsn_sac,
          },
        ],
      });
      markSampleInvoiceCreated();
      setSampleDone(true);
      router.push(`${ROUTES.INVOICES}/${invoice.id}`);
    } catch (err) {
      setSampleError(err instanceof Error ? err.message : "Could not create sample invoice");
    } finally {
      setSamplePending(false);
    }
  };

  return (
    <Card className="border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-base">{MSME_QUICK_START_COPY.TITLE[lang]}</CardTitle>
              <CardDescription>
                {getMsmeSegmentLabel(segmentId, lang)} · {actions.length}{" "}
                {MSME_QUICK_START_COPY.SUGGESTED_ACTIONS[lang]}
              </CardDescription>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            onClick={handleDismiss}
            aria-label={MSME_QUICK_START_COPY.DISMISS[lang]}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {actions.map((action) => {
          const href = action.assistantPrompt
            ? `${ROUTES.ASSISTANT}?${ASSISTANT_QUERY_PARAM}=${encodeURIComponent(action.assistantPrompt)}`
            : action.href;
          return (
            <Link
              key={action.label.en}
              href={href}
              className="inline-flex h-8 items-center rounded-md border border-input bg-background px-3 text-xs font-medium shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              {action.label[lang]}
              <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
            </Link>
          );
        })}
        {!sampleDone && (
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="h-8 text-xs"
            disabled={samplePending}
            onClick={handleSampleInvoice}
          >
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            {samplePending
              ? MSME_QUICK_START_COPY.SAMPLE_INVOICE_CREATING[lang]
              : MSME_QUICK_START_COPY.SAMPLE_INVOICE[lang]}
          </Button>
        )}
        {sampleError && <p className="w-full text-xs text-destructive">{sampleError}</p>}
      </CardContent>
    </Card>
  );
}
