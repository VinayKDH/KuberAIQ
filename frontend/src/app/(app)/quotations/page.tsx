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
import { useQuotations } from "@/features/quotations/hooks";
import { useDebounce } from "@/hooks/use-debounce";
import {
  DEFAULT_PAGE_SIZE,
  QUOTATION_COPY,
  QUOTATION_STATUS_FILTER_OPTIONS,
  QUOTATION_STATUS_LABELS,
  QUOTATION_STATUS_VARIANTS,
  ROUTES,
} from "@/lib/constants";
import { formatDate, formatINR } from "@/lib/format";

export default function QuotationsPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const debouncedSearch = useDebounce(search);
  const { data, isLoading, isError, error } = useQuotations({
    q: debouncedSearch || undefined,
    status: (statusFilter || undefined) as never,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{QUOTATION_COPY.TITLE}</h2>
          <p className="text-muted-foreground">{QUOTATION_COPY.DESCRIPTION}</p>
        </div>
        <Link href={ROUTES.QUOTATIONS_NEW}>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New quotation
          </Button>
        </Link>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search quotations…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select
          className="w-full sm:w-48"
          options={[...QUOTATION_STATUS_FILTER_OPTIONS]}
          value={statusFilter}
          onValueChange={setStatusFilter}
          aria-label="Filter by status"
        />
      </div>

      {isError && (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "Failed to load quotations"}
        </p>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Quote #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Issue date</TableHead>
              <TableHead>Valid until</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Total</TableHead>
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
                  No quotations found
                </TableCell>
              </TableRow>
            )}
            {data?.items.map((quotation) => (
              <TableRow key={quotation.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">
                  <Link href={ROUTES.QUOTATION_DETAIL(quotation.id)} className="hover:underline">
                    {quotation.quotation_number ?? "Draft"}
                  </Link>
                </TableCell>
                <TableCell>{quotation.customer?.name ?? "—"}</TableCell>
                <TableCell>{formatDate(quotation.issue_date)}</TableCell>
                <TableCell>{formatDate(quotation.valid_until)}</TableCell>
                <TableCell>
                  <Badge variant={QUOTATION_STATUS_VARIANTS[quotation.status] ?? "secondary"}>
                    {QUOTATION_STATUS_LABELS[quotation.status] ?? quotation.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">{formatINR(quotation.grand_total)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total > 0 && (
        <p className="text-sm text-muted-foreground">
          Showing {data.items.length} of {data.total} quotations
        </p>
      )}
    </div>
  );
}
