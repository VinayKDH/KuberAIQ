"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAdminSystemHealth, useResetDemoData } from "@/features/admin/hooks";
import { ADMIN_COPY, APP_NAME } from "@/lib/constants";

function StatusBadge({ ok }: { ok: boolean }) {
  return (
    <Badge variant={ok ? "default" : "secondary"}>{ok ? "Configured" : "Not set"}</Badge>
  );
}

export default function AdminSystemPage() {
  const { data, isLoading, isError } = useAdminSystemHealth();
  const resetDemo = useResetDemoData();

  if (isLoading) {
    return <p className="text-zinc-500">{ADMIN_COPY.LOADING}</p>;
  }

  if (isError || !data) {
    return <p className="text-red-400">{ADMIN_COPY.ERROR}</p>;
  }

  const modes = [
    { label: "Environment", value: data.environment },
    { label: "Auth", value: data.auth_mode },
    { label: "LLM", value: data.llm_mode },
    { label: "Blob storage", value: data.blob_mode },
    { label: "WhatsApp", value: data.whatsapp_mode },
    { label: "Billing", value: data.billing_mode },
  ];

  const integrations = [
    { label: "Google OAuth", ok: data.google_oauth_configured },
    { label: "Entra OAuth", ok: data.entra_oauth_configured },
    { label: "Azure OpenAI", ok: data.azure_openai_configured },
    { label: "Azure Blob", ok: data.azure_blob_configured },
    { label: "WhatsApp API", ok: data.whatsapp_configured },
    { label: "Razorpay", ok: data.razorpay_configured },
    { label: "Razorpay webhook", ok: data.razorpay_webhook_configured },
    { label: "Admin API key", ok: data.admin_api_key_configured },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{ADMIN_COPY.SYSTEM_TITLE}</h2>
        <p className="text-zinc-400">{ADMIN_COPY.SYSTEM_SUBTITLE}</p>
      </div>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardHeader>
          <CardTitle>{APP_NAME} deploy modes</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {modes.map((item) => (
            <div
              key={item.label}
              className="rounded-md border border-zinc-800 bg-zinc-900 px-4 py-3"
            >
              <p className="text-xs text-zinc-500">{item.label}</p>
              <p className="font-medium capitalize">{item.value}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardHeader>
          <CardTitle>Integration status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {integrations.map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <span>{item.label}</span>
              <StatusBadge ok={item.ok} />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardHeader>
          <CardTitle>Maintenance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-zinc-400">{ADMIN_COPY.RESET_DEMO_CONFIRM}</p>
          <Button
            variant="outline"
            className="border-zinc-700"
            disabled={resetDemo.isPending}
            onClick={() => {
              if (window.confirm(ADMIN_COPY.RESET_DEMO_CONFIRM)) {
                resetDemo.mutate();
              }
            }}
          >
            {ADMIN_COPY.RESET_DEMO}
          </Button>
          {resetDemo.isSuccess ? (
            <p className="text-sm text-emerald-400">{resetDemo.data?.message}</p>
          ) : null}
          {resetDemo.isError ? (
            <p className="text-sm text-red-400">
              {resetDemo.error instanceof Error ? resetDemo.error.message : ADMIN_COPY.ERROR}
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
