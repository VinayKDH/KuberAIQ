"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, IndianRupee, ScrollText } from "lucide-react";
import { AdvisorsPanel } from "@/components/settings/advisors-panel";
import { BillingSubscriptionPanel } from "@/components/settings/billing-subscription-panel";
import { StaffPanel } from "@/components/settings/staff-panel";
import { WhatsappCopilotPanel } from "@/components/settings/whatsapp-copilot-panel";
import { GstReportPanel } from "@/components/settings/gst-report-panel";
import { GstrFilingPanel } from "@/components/settings/gstr-filing-panel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api-client";
import { getStoredUser } from "@/lib/auth";
import { API_PATHS, PAYMENTS_SETTINGS, QUERY_KEYS, REMINDER_LANGUAGES, USER_ROLE } from "@/lib/constants";

interface CompanyProfile {
  id: string;
  legal_name: string;
  gstin: string | null;
  state_code: string;
  address: string | null;
  invoice_prefix: string;
  upi_id?: string | null;
  upi_payee_name?: string | null;
  auto_reminders_enabled?: boolean;
  default_reminder_language?: string;
}

interface AuditLogList {
  items: Array<{
    id: string;
    entity_type: string;
    action: string;
    created_at: string;
  }>;
  total: number;
}

export default function SettingsPage() {
  const user = getStoredUser();
  const { data: company, refetch } = useQuery({
    queryKey: QUERY_KEYS.COMPANY,
    queryFn: () => apiClient<CompanyProfile>(API_PATHS.COMPANY_ME),
  });
  const { data: auditLogs } = useQuery({
    queryKey: QUERY_KEYS.AUDIT_LOGS,
    queryFn: () => apiClient<AuditLogList>(API_PATHS.AUDIT_LOGS),
  });

  const [legalName, setLegalName] = useState("");
  const [gstin, setGstin] = useState("");
  const [address, setAddress] = useState("");
  const [invoicePrefix, setInvoicePrefix] = useState("INV");
  const [upiId, setUpiId] = useState("");
  const [upiPayeeName, setUpiPayeeName] = useState("");
  const [autoReminders, setAutoReminders] = useState(true);
  const [reminderLanguage, setReminderLanguage] = useState("en");
  const [saving, setSaving] = useState(false);
  const [paymentsSaving, setPaymentsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [paymentsMessage, setPaymentsMessage] = useState<string | null>(null);

  useEffect(() => {
    if (company) {
      setLegalName(company.legal_name);
      setGstin(company.gstin ?? "");
      setAddress(company.address ?? "");
      setInvoicePrefix(company.invoice_prefix);
      setUpiId(company.upi_id ?? "");
      setUpiPayeeName(company.upi_payee_name ?? "");
      setAutoReminders(company.auto_reminders_enabled ?? true);
      setReminderLanguage(company.default_reminder_language ?? "en");
    }
  }, [company]);

  const savePayments = async () => {
    setPaymentsSaving(true);
    setPaymentsMessage(null);
    try {
      await apiClient(API_PATHS.COMPANY_ME, {
        method: "PATCH",
        body: {
          upi_id: upiId.trim() || null,
          upi_payee_name: upiPayeeName.trim() || null,
          auto_reminders_enabled: autoReminders,
          default_reminder_language: reminderLanguage,
        },
      });
      setPaymentsMessage("Payment settings updated.");
      await refetch();
    } catch (err) {
      setPaymentsMessage(err instanceof Error ? err.message : "Update failed");
    } finally {
      setPaymentsSaving(false);
    }
  };

  const saveCompany = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await apiClient(API_PATHS.COMPANY_ME, {
        method: "PATCH",
        body: {
          legal_name: legalName,
          gstin: gstin.toUpperCase(),
          address,
          invoice_prefix: invoicePrefix,
        },
      });
      setMessage("Company profile updated.");
      await refetch();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const isCa = user?.role === USER_ROLE.CA;
  const isOwner = user?.role === USER_ROLE.OWNER;
  const defaultTab = isCa ? "reports" : "company";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">
          {isCa ? "GSTR reports and account" : "Manage your company and account preferences"}
        </p>
      </div>

      <Tabs defaultValue={defaultTab}>
        <TabsList>
          {!isCa && <TabsTrigger value="company">Company</TabsTrigger>}
          {!isCa && <TabsTrigger value="billing">Billing</TabsTrigger>}
          <TabsTrigger value="reports">Reports</TabsTrigger>
          {isOwner && !isCa && <TabsTrigger value="advisors">Advisors</TabsTrigger>}
          {isOwner && !isCa && <TabsTrigger value="staff">Staff</TabsTrigger>}
          {isOwner && !isCa && <TabsTrigger value="integrations">Integrations</TabsTrigger>}
          {!isCa && <TabsTrigger value="audit">Audit log</TabsTrigger>}
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>

        {!isCa && (
          <TabsContent value="company" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-muted-foreground" />
                  <CardTitle>Company Information</CardTitle>
                </div>
                <CardDescription>GST billing details used on invoices and reports</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="company-name">Company Name</Label>
                    <Input
                      id="company-name"
                      value={legalName}
                      onChange={(e) => setLegalName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gstin">GSTIN</Label>
                    <Input
                      id="gstin"
                      value={gstin}
                      onChange={(e) => setGstin(e.target.value.toUpperCase())}
                      maxLength={15}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="state">State Code</Label>
                    <Input id="state" value={company?.state_code ?? ""} disabled />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="prefix">Invoice Prefix</Label>
                    <Input
                      id="prefix"
                      value={invoicePrefix}
                      onChange={(e) => setInvoicePrefix(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Billing Address</Label>
                  <Textarea
                    id="address"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    rows={3}
                  />
                </div>
                {message && <p className="text-sm text-muted-foreground">{message}</p>}
                <Button onClick={saveCompany} disabled={saving || !isOwner}>
                  {saving ? "Saving…" : "Save company profile"}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <IndianRupee className="h-5 w-5 text-muted-foreground" />
                  <CardTitle>{PAYMENTS_SETTINGS.TITLE}</CardTitle>
                </div>
                <CardDescription>{PAYMENTS_SETTINGS.DESCRIPTION}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="upi-id">{PAYMENTS_SETTINGS.UPI_ID}</Label>
                    <Input
                      id="upi-id"
                      value={upiId}
                      onChange={(e) => setUpiId(e.target.value)}
                      placeholder="merchant@upi"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="upi-payee">{PAYMENTS_SETTINGS.UPI_PAYEE_NAME}</Label>
                    <Input
                      id="upi-payee"
                      value={upiPayeeName}
                      onChange={(e) => setUpiPayeeName(e.target.value)}
                      placeholder={company?.legal_name ?? "Business name"}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    id="auto-reminders"
                    type="checkbox"
                    checked={autoReminders}
                    onChange={(e) => setAutoReminders(e.target.checked)}
                    className="h-4 w-4 rounded border"
                  />
                  <Label htmlFor="auto-reminders">{PAYMENTS_SETTINGS.AUTO_REMINDERS}</Label>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reminder-language">{PAYMENTS_SETTINGS.DEFAULT_LANGUAGE}</Label>
                  <select
                    id="reminder-language"
                    value={reminderLanguage}
                    onChange={(e) => setReminderLanguage(e.target.value)}
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  >
                    {REMINDER_LANGUAGES.map((lang) => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                </div>
                {paymentsMessage && <p className="text-sm text-muted-foreground">{paymentsMessage}</p>}
                <Button onClick={savePayments} disabled={paymentsSaving || !isOwner}>
                  {paymentsSaving ? "Saving…" : PAYMENTS_SETTINGS.SAVE_LABEL}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {!isCa && (
          <TabsContent value="billing" className="space-y-4">
            <BillingSubscriptionPanel />
          </TabsContent>
        )}

        <TabsContent value="reports" className="space-y-4">
          <GstReportPanel />
          <GstrFilingPanel />
        </TabsContent>

        {isOwner && !isCa && (
          <TabsContent value="advisors" className="space-y-4">
            <AdvisorsPanel />
          </TabsContent>
        )}

        {isOwner && !isCa && (
          <TabsContent value="staff" className="space-y-4">
            <StaffPanel />
          </TabsContent>
        )}

        {isOwner && !isCa && (
          <TabsContent value="integrations" className="space-y-4">
            <WhatsappCopilotPanel isOwner={isOwner} />
          </TabsContent>
        )}

        {!isCa && (
          <TabsContent value="audit" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ScrollText className="h-5 w-5 text-muted-foreground" />
                  <CardTitle>Audit log</CardTitle>
                </div>
                <CardDescription>Recent create, update, and payment actions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {auditLogs?.items.length ? (
                  auditLogs.items.map((entry) => (
                    <div key={entry.id} className="rounded-md border p-3 text-sm">
                      <p className="font-medium">
                        {entry.action} · {entry.entity_type}
                      </p>
                      <p className="text-muted-foreground">{entry.created_at}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">No audit entries yet.</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="account" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Account</CardTitle>
              <CardDescription>Your profile and role</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input value={user?.full_name ?? ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input value={user?.email ?? ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Input value={user?.role ?? ""} disabled />
                </div>
              </div>
              <Separator />
              <p className="text-sm text-muted-foreground">
                Production sign-in uses Google. Link WhatsApp under Integrations to use the AI copilot on mobile.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
