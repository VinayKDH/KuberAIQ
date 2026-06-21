"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ADMIN_COPY, ROUTES } from "@/lib/constants";
import { verifyAdminKey } from "@/lib/admin-auth";

export default function AdminLoginPage() {
  const router = useRouter();
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const ok = await verifyAdminKey(apiKey);
    setLoading(false);
    if (ok) {
      router.replace(ROUTES.ADMIN_DASHBOARD);
      return;
    }
    setError(ADMIN_COPY.INVALID_KEY);
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-4">
      <Card className="w-full max-w-md border-zinc-800 bg-zinc-900 text-zinc-100">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800">
            <Shield className="h-6 w-6 text-emerald-400" />
          </div>
          <CardTitle>{ADMIN_COPY.LOGIN_TITLE}</CardTitle>
          <CardDescription className="text-zinc-400">{ADMIN_COPY.LOGIN_SUBTITLE}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="admin-key">{ADMIN_COPY.API_KEY_LABEL}</Label>
              <Input
                id="admin-key"
                type="password"
                autoComplete="off"
                placeholder={ADMIN_COPY.API_KEY_PLACEHOLDER}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="border-zinc-700 bg-zinc-950"
              />
            </div>
            {error ? <p className="text-sm text-red-400">{error}</p> : null}
            <Button type="submit" className="w-full" disabled={loading || !apiKey.trim()}>
              {loading ? ADMIN_COPY.SIGNING_IN : ADMIN_COPY.SIGN_IN}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
