"use client";

import { Lightbulb } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useMsmeSegment } from "@/features/company/hooks";
import { MSME_COMPLIANCE_TIPS } from "@/lib/constants";
import { getMsmeSegmentLabel } from "@/lib/msme-segment";
import { getPreferredLanguage } from "@/lib/i18n";

export function MsmeComplianceTipsCard() {
  const lang = getPreferredLanguage();
  const segmentId = useMsmeSegment();
  const tips = MSME_COMPLIANCE_TIPS[segmentId];

  return (
    <Card className="border-amber-500/30 bg-amber-50/30 dark:bg-amber-950/10">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-amber-600" />
          <CardTitle className="text-base">
            {lang === "hi" ? "आपके व्यवसाय के लिए टिप्स" : "Tips for your business"}
          </CardTitle>
        </div>
        <CardDescription>{getMsmeSegmentLabel(segmentId, lang)}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm text-muted-foreground">
          {tips.map((tip) => (
            <li key={tip.en} className="flex gap-2">
              <span className="text-amber-600">•</span>
              <span>{tip[lang]}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
