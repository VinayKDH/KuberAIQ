"use client";

import { useState } from "react";
import { UserPlus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdvisors, useInviteAdvisor, useRevokeAdvisor } from "@/features/ca/hooks";
import { CA_COPY } from "@/lib/constants";
import { formatApiError } from "@/lib/api-client";

function statusLabel(status: string): string {
  if (status === "PENDING") return CA_COPY.STATUS_PENDING;
  if (status === "ACTIVE") return CA_COPY.STATUS_ACTIVE;
  if (status === "REVOKED") return CA_COPY.STATUS_REVOKED;
  return status;
}

export function AdvisorsPanel() {
  const { data, isLoading } = useAdvisors();
  const inviteMutation = useInviteAdvisor();
  const revokeMutation = useRevokeAdvisor();
  const [email, setEmail] = useState("");
  const [firmName, setFirmName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await inviteMutation.mutateAsync({
        email: email.trim().toLowerCase(),
        ca_firm_name: firmName.trim() || undefined,
      });
      setMessage(CA_COPY.INVITE_SENT);
      setEmail("");
      setFirmName("");
    } catch (err) {
      setError(formatApiError(err, CA_COPY.INVITE_ERROR));
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <CardTitle>{CA_COPY.ADVISORS_TITLE}</CardTitle>
        </div>
        <CardDescription>{CA_COPY.ADVISORS_DESCRIPTION}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleInvite} className="space-y-4 rounded-md border p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="ca-email">{CA_COPY.CA_EMAIL}</Label>
              <Input
                id="ca-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="advisor@ca.kuberaiq.com"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ca-firm">{CA_COPY.CA_FIRM}</Label>
              <Input
                id="ca-firm"
                value={firmName}
                onChange={(e) => setFirmName(e.target.value)}
                placeholder="Sharma & Associates"
              />
            </div>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
          <Button type="submit" disabled={inviteMutation.isPending}>
            <UserPlus className="mr-2 h-4 w-4" />
            {inviteMutation.isPending ? "Sending…" : CA_COPY.INVITE_CA}
          </Button>
        </form>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading advisors…</p>
        ) : data?.items.length ? (
          <ul className="space-y-3">
            {data.items.map((advisor) => (
              <li
                key={advisor.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 text-sm"
              >
                <div>
                  <p className="font-medium">{advisor.ca_full_name ?? advisor.ca_email}</p>
                  <p className="text-muted-foreground">{advisor.ca_email}</p>
                  {advisor.ca_firm_name && (
                    <p className="text-xs text-muted-foreground">
                      {CA_COPY.FIRM_LABEL}: {advisor.ca_firm_name}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs">
                    {statusLabel(advisor.status)}
                  </span>
                  {advisor.status !== "REVOKED" && (
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={revokeMutation.isPending}
                      onClick={() => revokeMutation.mutate(advisor.id)}
                    >
                      {CA_COPY.REVOKE_CA}
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No advisors invited yet.</p>
        )}
      </CardContent>
    </Card>
  );
}
