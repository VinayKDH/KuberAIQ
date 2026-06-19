"use client";

import { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient, formatApiError } from "@/lib/api-client";
import { API_PATHS, INDIA_MOBILE_PHONE_REGEX, WHATSAPP_COPILOT_SETTINGS } from "@/lib/constants";

interface MeUser {
  whatsapp_phone?: string | null;
}

interface MeResponse {
  user: MeUser;
}

interface WhatsappCopilotPanelProps {
  isOwner: boolean;
}

function normalizeIndianMobileInput(raw: string): string {
  let digits = raw.replace(/[\s\-()]/g, "").replace(/^\+/, "");
  if (digits.startsWith("91") && digits.length === 12) {
    digits = digits.slice(2);
  }
  return digits;
}

function validateIndianMobile(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const normalized = normalizeIndianMobileInput(trimmed);
  if (!INDIA_MOBILE_PHONE_REGEX.test(normalized)) {
    return WHATSAPP_COPILOT_SETTINGS.PHONE_INVALID;
  }
  return null;
}

export function WhatsappCopilotPanel({ isOwner }: WhatsappCopilotPanelProps) {
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const me = await apiClient<MeResponse>(API_PATHS.ME);
        if (active) {
          setPhone(me.user.whatsapp_phone ?? "");
        }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const save = async () => {
    setSaving(true);
    setError(null);
    setMessage(null);
    const trimmed = phone.trim();
    const validationError = validateIndianMobile(trimmed);
    if (validationError) {
      setError(validationError);
      setSaving(false);
      return;
    }
    try {
      await apiClient(API_PATHS.ME_WHATSAPP_PHONE, {
        method: "PATCH",
        body: { phone: trimmed || null },
      });
      setMessage(trimmed ? WHATSAPP_COPILOT_SETTINGS.SAVED : WHATSAPP_COPILOT_SETTINGS.CLEARED);
    } catch (err) {
      setError(formatApiError(err, WHATSAPP_COPILOT_SETTINGS.SAVE_ERROR));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{WHATSAPP_COPILOT_SETTINGS.TITLE}</CardTitle>
        </div>
        <CardDescription>{WHATSAPP_COPILOT_SETTINGS.DESCRIPTION}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="wa-phone">{WHATSAPP_COPILOT_SETTINGS.PHONE_LABEL}</Label>
          <Input
            id="wa-phone"
            inputMode="numeric"
            placeholder="9876543210"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            disabled={!isOwner || loading}
          />
          <p className="text-xs text-muted-foreground">{WHATSAPP_COPILOT_SETTINGS.PHONE_HINT}</p>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {message && <p className="text-sm text-muted-foreground">{message}</p>}
        <Button onClick={save} disabled={!isOwner || saving || loading}>
          {saving ? "Saving…" : WHATSAPP_COPILOT_SETTINGS.SAVE_LABEL}
        </Button>
      </CardContent>
    </Card>
  );
}
