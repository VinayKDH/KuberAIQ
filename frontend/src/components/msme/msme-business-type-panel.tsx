"use client";

import { useEffect, useState } from "react";
import { Building2 } from "lucide-react";
import { MsmeSegmentPicker } from "@/components/msme/msme-segment-picker";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { MSME_QUICK_START_COPY, type MsmeLoginSegmentId } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import { getStoredMsmeSegment, setStoredMsmeSegment } from "@/lib/msme-segment";

export function MsmeBusinessTypePanel() {
  const lang = getPreferredLanguage();
  const [segmentId, setSegmentId] = useState<MsmeLoginSegmentId>("kirana");
  const [savedId, setSavedId] = useState<MsmeLoginSegmentId>("kirana");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const stored = getStoredMsmeSegment();
    setSegmentId(stored);
    setSavedId(stored);
  }, []);

  const handleSave = () => {
    setStoredMsmeSegment(segmentId);
    setSavedId(segmentId);
    setMessage(MSME_QUICK_START_COPY.SAVED[lang]);
    window.setTimeout(() => setMessage(null), 3000);
  };

  const dirty = segmentId !== savedId;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Building2 className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{MSME_QUICK_START_COPY.BUSINESS_TYPE[lang]}</CardTitle>
        </div>
        <CardDescription>{MSME_QUICK_START_COPY.BUSINESS_TYPE_DESC[lang]}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <MsmeSegmentPicker lang={lang} value={segmentId} onChange={setSegmentId} />
        {message && <p className="text-sm text-emerald-600">{message}</p>}
        <Button onClick={handleSave} disabled={!dirty}>
          Save business type
        </Button>
      </CardContent>
    </Card>
  );
}
