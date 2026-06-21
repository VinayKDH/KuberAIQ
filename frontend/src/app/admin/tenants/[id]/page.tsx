"use client";

import { useParams } from "next/navigation";

import { AdminMetricCard } from "@/components/admin/admin-metric-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminTenant, useUpdateTenantStatus } from "@/features/admin/hooks";
import { ADMIN_COPY } from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";

export default function AdminTenantDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { data, isLoading, isError } = useAdminTenant(id);
  const updateStatus = useUpdateTenantStatus();

  if (isLoading) {
    return <p className="text-zinc-500">{ADMIN_COPY.LOADING}</p>;
  }

  if (isError || !data) {
    return <p className="text-red-400">{ADMIN_COPY.ERROR}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">{data.legal_name}</h2>
          <p className="text-zinc-400">{data.owner_email ?? "No owner"}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={data.is_active ? "default" : "destructive"}>
            {data.is_active ? "Active" : "Suspended"}
          </Badge>
          <Button
            variant="outline"
            className="border-zinc-700"
            disabled={updateStatus.isPending}
            onClick={() =>
              updateStatus.mutate({ id: data.company_id, is_active: !data.is_active })
            }
          >
            {data.is_active ? ADMIN_COPY.SUSPEND : ADMIN_COPY.ACTIVATE}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <AdminMetricCard title="Users" value={data.user_count} />
        <AdminMetricCard title="Invoices" value={data.invoice_count} />
        <AdminMetricCard title="AI tokens (month)" value={data.ai_usage.tokens_this_month} />
        <AdminMetricCard
          title="Compliance overdue"
          value={data.compliance_overdue_count}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-zinc-800 bg-zinc-950">
          <CardHeader>
            <CardTitle>Company profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-zinc-300">
            <p>GSTIN: {data.gstin ?? "—"}</p>
            <p>State: {data.state_code}</p>
            <p>Segment: {data.msme_segment ?? "—"}</p>
            <p>Plan: {data.plan_code ?? "—"} ({data.subscription_status})</p>
            <p>Created: {formatDate(data.created_at)}</p>
            <p>Address: {data.address ?? "—"}</p>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-950">
          <CardHeader>
            <CardTitle>Users</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow className="border-zinc-800">
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.users.map((user) => (
                  <TableRow key={user.id} className="border-zinc-800">
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.role}</TableCell>
                    <TableCell>{user.is_active ? "Active" : "Inactive"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-950">
        <CardHeader>
          <CardTitle>Recent invoices</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-zinc-800">
                <TableHead>Number</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.recent_invoices.length ? (
                data.recent_invoices.map((inv) => (
                  <TableRow key={inv.id} className="border-zinc-800">
                    <TableCell>{inv.invoice_number ?? inv.id.slice(0, 8)}</TableCell>
                    <TableCell>{inv.status}</TableCell>
                    <TableCell>{formatDate(inv.issue_date)}</TableCell>
                    <TableCell className="text-right">{formatINR(inv.grand_total)}</TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} className="text-zinc-500">
                    {ADMIN_COPY.NO_DATA}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
