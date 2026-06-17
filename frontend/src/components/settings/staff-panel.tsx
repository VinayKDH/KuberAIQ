"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { UserPlus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient, formatApiError } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";

interface StaffPayload {
  users: Array<{ id: string; email: string; full_name?: string | null; role: string }>;
  invitations: Array<{ id: string; email: string; role: string; status: string }>;
}

export function StaffPanel() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const { data } = useQuery({
    queryKey: ["company", "staff"],
    queryFn: () => apiClient<StaffPayload>(API_PATHS.COMPANY_STAFF),
  });
  const invite = useMutation({
    mutationFn: () => apiClient(API_PATHS.COMPANY_STAFF, { method: "POST", body: { email, role: "STAFF" } }),
    onSuccess: () => {
      setMessage("Staff invite sent.");
      setEmail("");
      queryClient.invalidateQueries({ queryKey: ["company", "staff"] });
    },
    onError: (error) => setMessage(formatApiError(error, "Invite failed")),
  });
  const revoke = useMutation({
    mutationFn: (id: string) => apiClient(API_PATHS.COMPANY_STAFF_REVOKE(id), { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["company", "staff"] }),
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <CardTitle>Staff members</CardTitle>
        </div>
        <CardDescription>Invite team members to collaborate in this company workspace.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="staff-email">Staff email</Label>
          <Input
            id="staff-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="staff@yourcompany.com"
          />
        </div>
        <Button disabled={!email || invite.isPending} onClick={() => invite.mutate()}>
          <UserPlus className="mr-2 h-4 w-4" />
          Invite staff
        </Button>
        {message && <p className="text-sm text-muted-foreground">{message}</p>}

        {(data?.users?.length ?? 0) > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Current users</p>
            {data?.users.map((user) => (
              <div key={user.id} className="rounded border p-2 text-sm">
                {user.full_name || user.email} · {user.role}
              </div>
            ))}
          </div>
        )}
        {(data?.invitations?.length ?? 0) > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Pending invitations</p>
            {data?.invitations.map((inviteRow) => (
              <div key={inviteRow.id} className="flex items-center justify-between rounded border p-2 text-sm">
                <span>
                  {inviteRow.email} · {inviteRow.status}
                </span>
                {inviteRow.status === "PENDING" && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={revoke.isPending}
                    onClick={() => revoke.mutate(inviteRow.id)}
                  >
                    Revoke
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
