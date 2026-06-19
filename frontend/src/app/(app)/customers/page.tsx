"use client";

import Link from "next/link";
import { useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AddCustomerDialog } from "@/components/customers/add-customer-dialog";
import { StarterCustomersBanner } from "@/components/customers/starter-customers-banner";
import { useCustomers } from "@/features/customers/hooks";
import { useDebounce } from "@/hooks/use-debounce";
import { DEFAULT_PAGE_SIZE, MSME_SCREEN_COPY, ROUTES } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import { formatDate, formatPhone, maskGstin } from "@/lib/format";

export default function CustomersPage() {
  const lang = getPreferredLanguage();
  const copy = MSME_SCREEN_COPY.customers;
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search);
  const { data, isLoading, isError, error } = useCustomers({
    q: debouncedSearch || undefined,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{copy.title[lang]}</h2>
          <p className="text-muted-foreground">{copy.subtitle[lang]}</p>
        </div>
        <AddCustomerDialog />
      </div>

      <StarterCustomersBanner customerCount={data?.total ?? 0} />

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder={copy.search[lang]}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {isError && (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "Failed to load customers"}
        </p>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>GSTIN</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 5 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                  No customers found
                </TableCell>
              </TableRow>
            )}
            {data?.items.map((customer) => (
              <TableRow key={customer.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">
                  <Link href={ROUTES.CUSTOMER_DETAIL(customer.id)} className="hover:underline">
                    {customer.name}
                  </Link>
                </TableCell>
                <TableCell>{formatPhone(customer.phone)}</TableCell>
                <TableCell>{customer.email ?? "—"}</TableCell>
                <TableCell>{customer.gstin ? maskGstin(customer.gstin) : "—"}</TableCell>
                <TableCell>
                  {customer.created_at ? formatDate(customer.created_at) : "—"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total > 0 && (
        <p className="text-sm text-muted-foreground">
          Showing {data.items.length} of {data.total} customers
        </p>
      )}
    </div>
  );
}
