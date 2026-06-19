"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ASSISTANT_QUERY_PARAM,
  MSME_QUICK_START_ACTIONS,
  MSME_QUICK_START_COPY,
  ROUTES,
  type MsmeLoginSegmentId,
} from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import {
  dismissQuickStart,
  getMsmeSegmentLabel,
  getStoredMsmeSegment,
  isQuickStartDismissed,
} from "@/lib/msme-segment";

export function MsmeQuickStartCard() {
  const lang = getPreferredLanguage();
  const [visible, setVisible] = useState(false);
  const [segmentId, setSegmentId] = useState<MsmeLoginSegmentId>("kirana");

  useEffect(() => {
    if (isQuickStartDismissed()) return;
    setSegmentId(getStoredMsmeSegment());
    setVisible(true);
  }, []);

  if (!visible) return null;

  const actions = MSME_QUICK_START_ACTIONS[segmentId];

  const handleDismiss = () => {
    dismissQuickStart();
    setVisible(false);
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
                {getMsmeSegmentLabel(segmentId, lang)} · {actions.length} suggested actions
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
      </CardContent>
    </Card>
  );
}
