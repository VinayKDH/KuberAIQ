"use client";

import { useEffect, useState } from "react";
import { Check, Copy, MessageCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient, formatApiError } from "@/lib/api-client";
import {
  API_PATHS,
  HEALTH_INTEGRATIONS_URL,
  INDIA_MOBILE_PHONE_REGEX,
  WHATSAPP_COPILOT_SETTINGS,
  WHATSAPP_WEBHOOK_URL,
} from "@/lib/constants";

interface MeUser {
  whatsapp_phone?: string | null;
}

interface MeResponse {
  user: MeUser;
}

interface IntegrationsHealth {
  whatsapp_mode?: string;
  whatsapp_configured?: boolean;
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
  const [whatsappMode, setWhatsappMode] = useState<string | null>(null);
  const [webhookCopied, setWebhookCopied] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [me, healthRes] = await Promise.all([
          apiClient<MeResponse>(API_PATHS.ME),
          fetch(HEALTH_INTEGRATIONS_URL).then((r) => (r.ok ? r.json() : null)),
        ]);
        if (active) {
          setPhone(me.user.whatsapp_phone ?? "");
          if (healthRes) {
            const health = healthRes as IntegrationsHealth;
            setWhatsappMode(health.whatsapp_mode ?? null);
          }
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

  const copyWebhook = async () => {
    try {
      await navigator.clipboard.writeText(WHATSAPP_WEBHOOK_URL);
      setWebhookCopied(true);
      setTimeout(() => setWebhookCopied(false), 2000);
    } catch {
      setError(WHATSAPP_COPILOT_SETTINGS.HEALTH_ERROR);
    }
  };

  const isLinked = Boolean(phone.trim());
  const modeLabel =
    whatsappMode === "live"
      ? WHATSAPP_COPILOT_SETTINGS.MODE_LIVE
      : whatsappMode === "mock"
        ? WHATSAPP_COPILOT_SETTINGS.MODE_MOCK
        : WHATSAPP_COPILOT_SETTINGS.MODE_UNKNOWN;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-muted-foreground" />
            <CardTitle>{WHATSAPP_COPILOT_SETTINGS.TITLE}</CardTitle>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant={isLinked ? "default" : "secondary"}>
              {isLinked
                ? WHATSAPP_COPILOT_SETTINGS.STATUS_LINKED
                : WHATSAPP_COPILOT_SETTINGS.STATUS_NOT_LINKED}
            </Badge>
            {whatsappMode && (
              <Badge variant={whatsappMode === "live" ? "default" : "outline"}>
                {WHATSAPP_COPILOT_SETTINGS.MODE_LABEL}: {modeLabel}
              </Badge>
            )}
          </div>
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

        <div className="space-y-2 rounded-md border bg-muted/30 p-3">
          <Label className="text-xs">{WHATSAPP_COPILOT_SETTINGS.WEBHOOK_LABEL}</Label>
          <div className="flex flex-wrap items-center gap-2">
            <code className="flex-1 break-all text-xs">{WHATSAPP_WEBHOOK_URL}</code>
            <Button type="button" size="sm" variant="outline" onClick={copyWebhook}>
              {webhookCopied ? (
                <Check className="mr-1 h-3 w-3" />
              ) : (
                <Copy className="mr-1 h-3 w-3" />
              )}
              {webhookCopied ? WHATSAPP_COPILOT_SETTINGS.WEBHOOK_COPIED : "Copy"}
            </Button>
          </div>
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
