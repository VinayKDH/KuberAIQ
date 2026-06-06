"use client";

import { AlertCircle, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useCollectionsDashboard, useOverdueInvoices } from "@/features/collections/hooks";
import { DEFAULT_PAGE_SIZE } from "@/lib/constants";
import { formatDate, formatINR, formatPhone } from "@/lib/format";

export default function CollectionsPage() {
  const { data: dashboard, isLoading: dashboardLoading } = useCollectionsDashboard();
  const { data, isLoading, isError, error } = useOverdueInvoices({
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    sort: "-days_overdue",
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Collections</h2>
        <p className="text-muted-foreground">Track and follow up on overdue invoices</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Overdue
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-2xl font-bold text-destructive">
                {formatINR(dashboard?.total_overdue ?? data?.items.reduce((s, i) => s + i.amount_due, 0) ?? 0)}
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Overdue Invoices
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-2xl font-bold">
                {dashboard?.overdue_count ?? data?.total ?? 0}
              </p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Reminded Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboardLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <p className="text-2xl font-bold">{dashboard?.reminded_today ?? 0}</p>
            )}
          </CardContent>
        </Card>
      </div>

      {isError && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {error instanceof Error ? error.message : "Failed to load overdue invoices"}
        </div>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Invoice #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Due Date</TableHead>
              <TableHead>Days Overdue</TableHead>
              <TableHead className="text-right">Amount Due</TableHead>
              <TableHead>Last Reminder</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="h-24 text-center text-muted-foreground">
                  No overdue invoices — great job!
                </TableCell>
              </TableRow>
            )}
            {data?.items.map((invoice) => (
              <TableRow key={invoice.id}>
                <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                <TableCell>{invoice.customer_name}</TableCell>
                <TableCell>{formatPhone(invoice.customer_phone)}</TableCell>
                <TableCell>{formatDate(invoice.due_date)}</TableCell>
                <TableCell>
                  <Badge variant="destructive">{invoice.days_overdue}d</Badge>
                </TableCell>
                <TableCell className="text-right">{formatINR(invoice.amount_due)}</TableCell>
                <TableCell>
                  {invoice.last_reminder_at
                    ? formatDate(invoice.last_reminder_at)
                    : "Never"}
                </TableCell>
                <TableCell>
                  <Button variant="outline" size="sm" disabled>
                    <Send className="mr-1 h-3 w-3" />
                    Remind
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
