"use client";

import { useRouter } from "next/navigation";
import { Building2, Check, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAcceptCaInvite, useCaClients, useSwitchCaContext } from "@/features/ca/hooks";
import { CA_COPY, ROUTES } from "@/lib/constants";
import { formatApiError } from "@/lib/api-client";
import { useState } from "react";

export default function CaClientsPage() {
  const router = useRouter();
  const { data, isLoading, refetch } = useCaClients();
  const acceptMutation = useAcceptCaInvite();
  const switchMutation = useSwitchCaContext();
  const [error, setError] = useState<string | null>(null);

  const pending = data?.items.filter((item) => item.status === "PENDING") ?? [];
  const active = data?.items.filter((item) => item.status === "ACTIVE") ?? [];

  const handleAccept = async (assignmentId: string) => {
    setError(null);
    try {
      await acceptMutation.mutateAsync(assignmentId);
      await refetch();
    } catch (err) {
      setError(formatApiError(err, "Could not accept invitation"));
    }
  };

  const handleOpen = async (companyId: string) => {
    setError(null);
    try {
      await switchMutation.mutateAsync(companyId);
      router.push(ROUTES.COMPLIANCE);
    } catch (err) {
      setError(formatApiError(err, "Could not open client"));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">{CA_COPY.CLIENTS_TITLE}</h2>
        <p className="text-muted-foreground">{CA_COPY.CLIENTS_DESCRIPTION}</p>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading clients…</p>
      ) : (
        <>
          {pending.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>{CA_COPY.PENDING_INVITES}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {pending.map((item) => (
                  <div
                    key={item.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                  >
                    <div>
                      <p className="font-medium">{item.company_name ?? "MSME client"}</p>
                      {item.gstin && (
                        <p className="text-sm text-muted-foreground">GSTIN {item.gstin}</p>
                      )}
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleAccept(item.id)}
                      disabled={acceptMutation.isPending}
                    >
                      <Check className="mr-2 h-4 w-4" />
                      {CA_COPY.ACCEPT_INVITE}
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>{CA_COPY.ACTIVE_CLIENTS}</CardTitle>
              <CardDescription>
                Open a client to view compliance calendar and download GSTR reports.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {active.length ? (
                active.map((item) => (
                  <div
                    key={item.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3"
                  >
                    <div className="flex items-start gap-3">
                      <Building2 className="mt-0.5 h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{item.company_name}</p>
                        {item.gstin && (
                          <p className="text-sm text-muted-foreground">GSTIN {item.gstin}</p>
                        )}
                        {item.ca_firm_name && (
                          <p className="text-xs text-muted-foreground">
                            {CA_COPY.FIRM_LABEL}: {item.ca_firm_name}
                          </p>
                        )}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      onClick={() => handleOpen(item.company_id)}
                      disabled={switchMutation.isPending}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      {CA_COPY.OPEN_CLIENT}
                    </Button>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">{CA_COPY.NO_CLIENTS}</p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
