"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAdminTenants } from "@/features/admin/hooks";
import { ADMIN_COPY, DEFAULT_PAGE_SIZE, ROUTES } from "@/lib/constants";
import { formatDate } from "@/lib/format";

type Filter = "all" | "active" | "suspended";

export default function AdminTenantsPage() {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [page, setPage] = useState(1);

  const activeOnly = filter === "all" ? undefined : filter === "active";

  const { data, isLoading, isError } = useAdminTenants({
    page,
    page_size: DEFAULT_PAGE_SIZE,
    search: search || undefined,
    active_only: activeOnly,
  });

  const totalPages = useMemo(() => {
    if (!data) return 1;
    return Math.max(1, Math.ceil(data.total / data.page_size));
  }, [data]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">{ADMIN_COPY.TENANTS_TITLE}</h2>
        <p className="text-zinc-400">{ADMIN_COPY.TENANTS_SUBTITLE}</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Input
          placeholder={ADMIN_COPY.SEARCH_PLACEHOLDER}
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="max-w-sm border-zinc-700 bg-zinc-950"
        />
        {(["all", "active", "suspended"] as Filter[]).map((value) => (
          <Button
            key={value}
            size="sm"
            variant={filter === value ? "default" : "outline"}
            className={filter !== value ? "border-zinc-700 bg-transparent" : undefined}
            onClick={() => {
              setFilter(value);
              setPage(1);
            }}
          >
            {value === "all"
              ? ADMIN_COPY.FILTER_ALL
              : value === "active"
                ? ADMIN_COPY.FILTER_ACTIVE
                : ADMIN_COPY.FILTER_SUSPENDED}
          </Button>
        ))}
      </div>

      {isError ? <p className="text-red-400">{ADMIN_COPY.ERROR}</p> : null}

      <div className="rounded-lg border border-zinc-800">
        <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 hover:bg-transparent">
              <TableHead>Company</TableHead>
              <TableHead>GSTIN</TableHead>
              <TableHead>Segment</TableHead>
              <TableHead>Users</TableHead>
              <TableHead>Invoices</TableHead>
              <TableHead>Subscription</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last activity</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={8} className="text-zinc-500">
                  {ADMIN_COPY.LOADING}
                </TableCell>
              </TableRow>
            ) : data?.items.length ? (
              data.items.map((tenant) => (
                <TableRow key={tenant.company_id} className="border-zinc-800">
                  <TableCell>
                    <Link
                      href={ROUTES.ADMIN_TENANT_DETAIL(tenant.company_id)}
                      className="font-medium text-emerald-400 hover:underline"
                    >
                      {tenant.legal_name}
                    </Link>
                    <p className="text-xs text-zinc-500">{tenant.owner_email}</p>
                  </TableCell>
                  <TableCell>{tenant.gstin ?? "—"}</TableCell>
                  <TableCell>{tenant.msme_segment ?? "—"}</TableCell>
                  <TableCell>{tenant.user_count}</TableCell>
                  <TableCell>{tenant.invoice_count}</TableCell>
                  <TableCell>{tenant.subscription_status}</TableCell>
                  <TableCell>
                    <Badge variant={tenant.is_active ? "default" : "destructive"}>
                      {tenant.is_active ? "Active" : "Suspended"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-zinc-400">
                    {tenant.last_activity_at ? formatDate(tenant.last_activity_at) : "—"}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={8} className="text-zinc-500">
                  {ADMIN_COPY.NO_DATA}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {data && data.total > data.page_size ? (
        <div className="flex items-center justify-between">
          <p className="text-sm text-zinc-500">
            Page {page} of {totalPages} · {data.total} tenants
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              className="border-zinc-700"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="border-zinc-700"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
