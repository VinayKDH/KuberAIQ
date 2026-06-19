"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateComplianceProfile } from "@/features/compliance/hooks";
import { MsmeSegmentPicker } from "@/components/msme/msme-segment-picker";
import {
  API_PATHS,
  APP_NAME,
  COMPLIANCE_ENTITY_TYPES,
  COMPLIANCE_GSTR1_FREQUENCIES,
  COMPLIANCE_TURNOVER_BANDS,
  ONBOARDING_COPY,
  PAYMENTS_SETTINGS,
  REMINDER_LANGUAGES,
  ROUTES,
  STORAGE_KEYS,
  type MsmeLoginSegmentId,
} from "@/lib/constants";
import { useCanonicalOriginRedirect } from "@/hooks/use-canonical-origin";
import { apiClient, formatApiError } from "@/lib/api-client";
import { clearSession, storeSession, type AuthTokens } from "@/lib/auth";
import { getStoredMsmeSegment, setStoredMsmeSegment } from "@/lib/msme-segment";
import { getPreferredLanguage } from "@/lib/i18n";
import { postLoginRoute, type MeGate } from "@/lib/session-routing";

const TOTAL_STEPS = 3;

export default function OnboardingPage() {
  const router = useRouter();
  const redirecting = useCanonicalOriginRedirect();
  const complianceMutation = useUpdateComplianceProfile();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [legalName, setLegalName] = useState("");
  const [gstin, setGstin] = useState("");
  const [address, setAddress] = useState("");
  const [invoicePrefix, setInvoicePrefix] = useState("INV");

  const [entityType, setEntityType] = useState("PROPRIETORSHIP");
  const [turnoverBand, setTurnoverBand] = useState("");
  const [gstr1Frequency, setGstr1Frequency] = useState("MONTHLY");

  const [upiId, setUpiId] = useState("");
  const [upiPayeeName, setUpiPayeeName] = useState("");
  const [autoReminders, setAutoReminders] = useState(true);
  const [reminderLanguage, setReminderLanguage] = useState("en");
  const [msmeSegment, setMsmeSegment] = useState<MsmeLoginSegmentId>("kirana");
  const lang = getPreferredLanguage();

  useEffect(() => {
    setMsmeSegment(getStoredMsmeSegment());
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)) {
      router.replace(ROUTES.LOGIN);
      return;
    }
    apiClient<MeGate>(API_PATHS.ME)
      .then((me) => {
        const redirect = postLoginRoute(me);
        if (redirect !== ROUTES.ONBOARDING) {
          router.replace(redirect);
        }
      })
      .catch(() => {
        clearSession();
        router.replace(ROUTES.LOGIN);
      });
  }, [router]);

  const handleCompanySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await apiClient<AuthTokens>(API_PATHS.COMPANY_ONBOARD, {
        method: "POST",
        body: {
          legal_name: legalName,
          gstin: gstin.toUpperCase(),
          address,
          invoice_prefix: invoicePrefix,
        },
      });
      storeSession(tokens);
      setUpiPayeeName(legalName);
      setStep(2);
    } catch (err) {
      setError(formatApiError(err, "Setup failed"));
    } finally {
      setLoading(false);
    }
  };

  const saveCompliance = async (skip = false) => {
    setError(null);
    if (skip) {
      setStep(3);
      return;
    }
    if (!turnoverBand) {
      setError("Select your annual turnover band to unlock compliance tracking.");
      return;
    }
    setLoading(true);
    try {
      await complianceMutation.mutateAsync({
        entity_type: entityType,
        turnover_band: turnoverBand,
        gstr1_filing_frequency: gstr1Frequency,
      });
      setStep(3);
    } catch (err) {
      setError(formatApiError(err, "Could not save compliance profile"));
    } finally {
      setLoading(false);
    }
  };

  const finishOnboarding = async (skip = false) => {
    setError(null);
    setLoading(true);
    try {
      if (!skip) {
        setStoredMsmeSegment(msmeSegment);
        await apiClient(API_PATHS.COMPANY_ME, {
          method: "PATCH",
          body: {
            msme_segment: msmeSegment,
            ...(upiId.trim()
              ? {
                  upi_id: upiId.trim(),
                  upi_payee_name: upiPayeeName.trim() || legalName,
                  auto_reminders_enabled: autoReminders,
                  default_reminder_language: reminderLanguage,
                }
              : {}),
          },
        });
      }
      router.replace(ROUTES.DASHBOARD);
    } catch (err) {
      setError(formatApiError(err, "Could not save payment settings"));
    } finally {
      setLoading(false);
    }
  };

  if (redirecting) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4 text-sm text-muted-foreground">
        Redirecting to www.kuberaiq.com…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <p className="text-xs font-medium text-primary">
            {ONBOARDING_COPY.PROGRESS(step, TOTAL_STEPS)}
          </p>
          <CardTitle>
            {step === 1 && ONBOARDING_COPY.STEP_COMPANY}
            {step === 2 && ONBOARDING_COPY.STEP_COMPLIANCE}
            {step === 3 && ONBOARDING_COPY.STEP_PAYMENTS}
          </CardTitle>
          <CardDescription>
            {step === 1 && ONBOARDING_COPY.STEP_COMPANY_DESC}
            {step === 2 && ONBOARDING_COPY.STEP_COMPLIANCE_DESC}
            {step === 3 && ONBOARDING_COPY.STEP_PAYMENTS_DESC}
          </CardDescription>
          <div className="flex gap-2 pt-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1.5 flex-1 rounded-full ${s <= step ? "bg-primary" : "bg-muted"}`}
              />
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <form onSubmit={handleCompanySubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>{ONBOARDING_COPY.STEP_SEGMENT}</Label>
                <p className="text-xs text-muted-foreground">{ONBOARDING_COPY.STEP_SEGMENT_DESC}</p>
                <MsmeSegmentPicker
                  lang={lang}
                  value={msmeSegment}
                  onChange={(id) => {
                    setMsmeSegment(id);
                    setStoredMsmeSegment(id);
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="legal-name">Legal name</Label>
                <Input
                  id="legal-name"
                  value={legalName}
                  onChange={(e) => setLegalName(e.target.value)}
                  placeholder="Sharma Traders"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="gstin">GSTIN</Label>
                <Input
                  id="gstin"
                  value={gstin}
                  onChange={(e) => setGstin(e.target.value)}
                  maxLength={15}
                  placeholder="27AAAAA0000A1Z5"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Business address</Label>
                <Textarea
                  id="address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="prefix">Invoice prefix</Label>
                <Input
                  id="prefix"
                  value={invoicePrefix}
                  onChange={(e) => setInvoicePrefix(e.target.value)}
                  maxLength={10}
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Saving…" : ONBOARDING_COPY.CONTINUE}
              </Button>
            </form>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Entity type</Label>
                <Select
                  value={entityType}
                  options={COMPLIANCE_ENTITY_TYPES.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                  onValueChange={setEntityType}
                />
              </div>
              <div className="space-y-2">
                <Label>Annual turnover band</Label>
                <Select
                  value={turnoverBand}
                  placeholder="Select turnover band"
                  options={COMPLIANCE_TURNOVER_BANDS.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                  onValueChange={setTurnoverBand}
                />
              </div>
              <div className="space-y-2">
                <Label>GSTR-1 filing frequency</Label>
                <Select
                  value={gstr1Frequency}
                  options={COMPLIANCE_GSTR1_FREQUENCIES.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                  onValueChange={setGstr1Frequency}
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  disabled={loading}
                  onClick={() => saveCompliance(true)}
                >
                  {ONBOARDING_COPY.SKIP}
                </Button>
                <Button
                  type="button"
                  className="flex-1"
                  disabled={loading}
                  onClick={() => saveCompliance(false)}
                >
                  {loading ? "Saving…" : ONBOARDING_COPY.CONTINUE}
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="upi-id">{PAYMENTS_SETTINGS.UPI_ID}</Label>
                <Input
                  id="upi-id"
                  value={upiId}
                  onChange={(e) => setUpiId(e.target.value)}
                  placeholder="yourbusiness@upi"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="upi-payee">{PAYMENTS_SETTINGS.UPI_PAYEE_NAME}</Label>
                <Input
                  id="upi-payee"
                  value={upiPayeeName}
                  onChange={(e) => setUpiPayeeName(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-3 rounded-md border p-3">
                <input
                  id="auto-reminders"
                  type="checkbox"
                  checked={autoReminders}
                  onChange={(e) => setAutoReminders(e.target.checked)}
                  className="h-4 w-4"
                />
                <Label htmlFor="auto-reminders">{PAYMENTS_SETTINGS.AUTO_REMINDERS}</Label>
              </div>
              <div className="space-y-2">
                <Label>{PAYMENTS_SETTINGS.DEFAULT_LANGUAGE}</Label>
                <Select
                  value={reminderLanguage}
                  options={REMINDER_LANGUAGES.map((item) => ({
                    value: item.value,
                    label: item.label,
                  }))}
                  onValueChange={setReminderLanguage}
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  disabled={loading}
                  onClick={() => finishOnboarding(true)}
                >
                  {ONBOARDING_COPY.SKIP}
                </Button>
                <Button
                  type="button"
                  className="flex-1"
                  disabled={loading}
                  onClick={() => finishOnboarding(false)}
                >
                  {loading ? "Saving…" : ONBOARDING_COPY.FINISH}
                </Button>
              </div>
            </div>
          )}

          <p className="mt-6 text-center text-xs text-muted-foreground">
            Setting up {APP_NAME} for your business ·{" "}
            <Link href={ROUTES.COMPLIANCE} className="underline">
              compliance help
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
