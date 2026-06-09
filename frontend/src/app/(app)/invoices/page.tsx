"use client";

import Link from "next/link";
import { useState } from "react";
import { Plus, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useInvoices } from "@/features/invoices/hooks";
import { useDebounce } from "@/hooks/use-debounce";
import {
  DEFAULT_PAGE_SIZE,
  INVOICE_STATUS_FILTER_OPTIONS,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_VARIANTS,
  ROUTES,
} from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";

export default function InvoicesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const debouncedSearch = useDebounce(search);
  const { data, isLoading, isError, error } = useInvoices({
    q: debouncedSearch || undefined,
    status: statusFilter || undefined,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    sort: "-issue_date",
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Invoices</h2>
          <p className="text-muted-foreground">Manage GST invoices and payments</p>
        </div>
        <Link href={ROUTES.INVOICES_NEW}>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Invoice
          </Button>
        </Link>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search invoices…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          className="w-full sm:w-48"
          options={[...INVOICE_STATUS_FILTER_OPTIONS]}
          value={statusFilter}
          onValueChange={setStatusFilter}
          aria-label="Filter by status"
        />
      </div>

      {isError && (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "Failed to load invoices"}
        </p>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Invoice #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Issue Date</TableHead>
              <TableHead>Due Date</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Amount Due</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                  No invoices found
                </TableCell>
              </TableRow>
            )}
            {data?.items.map((invoice) => (
              <TableRow key={invoice.id} className="cursor-pointer hover:bg-muted/50">
                <TableCell className="font-medium">
                  <Link href={ROUTES.INVOICE_DETAIL(invoice.id)} className="hover:underline">
                    {invoice.invoice_number ?? "Draft"}
                  </Link>
                </TableCell>
                <TableCell>{invoice.customer?.name ?? "—"}</TableCell>
                <TableCell>{formatDate(invoice.issue_date)}</TableCell>
                <TableCell>{formatDate(invoice.due_date)}</TableCell>
                <TableCell>
                  <Badge variant={INVOICE_STATUS_VARIANTS[invoice.status] ?? "secondary"}>
                    {INVOICE_STATUS_LABELS[invoice.status] ?? invoice.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">{formatINR(invoice.amount_due)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total > 0 && (
        <p className="text-sm text-muted-foreground">
          Showing {data.items.length} of {data.total} invoices
        </p>
      )}
    </div>
  );
}
