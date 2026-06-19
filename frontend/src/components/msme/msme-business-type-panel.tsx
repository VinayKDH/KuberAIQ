"use client";

import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { MsmeSegmentPicker } from "@/components/msme/msme-segment-picker";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCompanyProfile } from "@/features/company/hooks";
import { MSME_QUICK_START_COPY, QUERY_KEYS, type MsmeLoginSegmentId } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import {
  persistMsmeSegment,
  resolveMsmeSegment,
} from "@/lib/msme-segment";

export function MsmeBusinessTypePanel() {
  const lang = getPreferredLanguage();
  const queryClient = useQueryClient();
  const { data: company } = useCompanyProfile();
  const [segmentId, setSegmentId] = useState<MsmeLoginSegmentId>("kirana");
  const [savedId, setSavedId] = useState<MsmeLoginSegmentId>("kirana");
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const resolved = resolveMsmeSegment(company?.msme_segment);
    setSegmentId(resolved);
    setSavedId(resolved);
  }, [company?.msme_segment]);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await persistMsmeSegment(segmentId);
      setSavedId(segmentId);
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.COMPANY });
      setMessage(MSME_QUICK_START_COPY.SAVED[lang]);
      window.setTimeout(() => setMessage(null), 3000);
    } catch {
      setMessage("Could not save business type.");
    } finally {
      setSaving(false);
    }
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
        {message && (
          <p className={`text-sm ${message.includes("Could") ? "text-destructive" : "text-emerald-600"}`}>
            {message}
          </p>
        )}
        <Button onClick={handleSave} disabled={!dirty || saving}>
          {saving ? "Saving…" : lang === "hi" ? "व्यवसाय प्रकार सहेजें" : "Save business type"}
        </Button>
      </CardContent>
    </Card>
  );
}
