"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Info, Phone, Send } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useBulkReminderPreview,
  useBulkSendReminders,
  useCallToday,
  useCollectionsDashboard,
  useOverdueInvoices,
  useReminderPreview,
  useSendReminder,
} from "@/features/collections/hooks";
import { apiClient } from "@/lib/api-client";
import { API_PATHS, COLLECTIONS_COPY, DEFAULT_PAGE_SIZE, MSME_SCREEN_COPY, QUERY_KEYS, ROUTES } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import { formatDate, formatINR, formatPhone } from "@/lib/format";

interface CompanyReminderSettings {
  auto_reminders_enabled?: boolean;
  default_reminder_language?: string;
}

export default function CollectionsPage() {
  const lang = getPreferredLanguage();
  const copy = MSME_SCREEN_COPY.collections;
  const { data: company } = useQuery({
    queryKey: QUERY_KEYS.COMPANY,
    queryFn: () => apiClient<CompanyReminderSettings>(API_PATHS.COMPANY_ME),
  });
  const { data: dashboard, isLoading: dashboardLoading } = useCollectionsDashboard();
  const { data: callToday, isLoading: callTodayLoading } = useCallToday();
  const { data, isLoading, isError, error } = useOverdueInvoices({
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    sort: "-days_overdue",
  });
  const bulkPreview = useBulkReminderPreview();
  const bulkSend = useBulkSendReminders();

  const [bulkOpen, setBulkOpen] = useState(false);
  const [reminderTarget, setReminderTarget] = useState<string | null>(null);
  const [reminderLanguage, setReminderLanguage] = useState<"en" | "hi">("en");
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const lang = company?.default_reminder_language;
    if (lang === "hi" || lang === "en") {
      setReminderLanguage(lang);
    }
  }, [company?.default_reminder_language]);
  const preview = useReminderPreview(reminderTarget ?? "", !!reminderTarget, reminderLanguage);
  const sendReminder = useSendReminder(reminderLanguage);

  const totalOverdue =
    dashboard?.total_overdue ??
    data?.items.reduce((sum, invoice) => sum + Number(invoice.amount_due), 0) ??
    0;

  async function handleBulkPreview() {
    setActionError(null);
    try {
      await bulkPreview.mutateAsync();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to load preview");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{copy.title[lang]}</h2>
          <p className="text-muted-foreground">{copy.subtitle[lang]}</p>
        </div>
        <Dialog
          open={bulkOpen}
          onOpenChange={(open) => {
            setBulkOpen(open);
            if (open) {
              void handleBulkPreview();
            }
          }}
        >
          <DialogTrigger asChild>
            <Button variant="outline" disabled={(data?.total ?? 0) === 0}>
              <Send className="mr-2 h-4 w-4" />
              Remind all overdue
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Send bulk reminders</DialogTitle>
              <DialogDescription>
                WhatsApp reminders will be sent to all eligible overdue invoices.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              {bulkPreview.isPending && <Skeleton className="h-16 w-full" />}
              {bulkPreview.data && (
                <div className="rounded-md border p-4 text-sm">
                  <p>
                    <span className="font-medium">{bulkPreview.data.count}</span> invoices ·{" "}
                    {formatINR(bulkPreview.data.total_outstanding)} outstanding
                  </p>
                </div>
              )}
              <Button
                className="w-full"
                disabled={bulkSend.isPending || !bulkPreview.data?.count}
                onClick={async () => {
                  setActionError(null);
                  try {
                    await bulkSend.mutateAsync();
                    setBulkOpen(false);
                  } catch (err) {
                    setActionError(err instanceof Error ? err.message : "Bulk send failed");
                  }
                }}
              >
                Confirm send
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {actionError && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          {actionError}
        </div>
      )}

      <div className="flex items-start gap-2 rounded-md border border-muted bg-muted/40 p-4 text-sm text-muted-foreground">
        <Info className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          {company?.auto_reminders_enabled ?? true
            ? COLLECTIONS_COPY.AUTO_REMINDERS_ON
            : COLLECTIONS_COPY.AUTO_REMINDERS_OFF}
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Phone className="h-5 w-5 text-muted-foreground" />
            <CardTitle>{COLLECTIONS_COPY.CALL_TODAY_TITLE}</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">{COLLECTIONS_COPY.CALL_TODAY_DESCRIPTION}</p>
        </CardHeader>
        <CardContent>
          {callTodayLoading && <Skeleton className="h-24 w-full" />}
          {!callTodayLoading && (!callToday || callToday.length === 0) && (
            <p className="text-sm text-muted-foreground">{COLLECTIONS_COPY.CALL_TODAY_EMPTY}</p>
          )}
          {!callTodayLoading && callToday && callToday.length > 0 && (
            <div className="space-y-3">
              {callToday.map((invoice) => {
                const urgency =
                  invoice.days_overdue > 0
                    ? `${invoice.days_overdue}d ${COLLECTIONS_COPY.OVERDUE.toLowerCase()}`
                    : invoice.days_until_due === 0
                      ? COLLECTIONS_COPY.DUE_TODAY
                      : `${invoice.days_until_due}d ${COLLECTIONS_COPY.DUE_SOON.toLowerCase()}`;
                return (
                  <div
                    key={invoice.id}
                    className="flex flex-col gap-3 rounded-md border p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="space-y-1">
                      <p className="font-medium">
                        <Link href={ROUTES.INVOICE_DETAIL(invoice.id)} className="hover:underline">
                          {invoice.invoice_number ?? "Invoice"}
                        </Link>
                        {" · "}
                        {invoice.customer_name}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatINR(invoice.amount_due)} · {urgency}
                        {invoice.customer_phone ? ` · ${formatPhone(invoice.customer_phone)}` : ""}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setActionError(null);
                        setReminderTarget(invoice.id);
                      }}
                    >
                      <Send className="mr-1 h-3 w-3" />
                      Remind
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

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
              <p className="text-2xl font-bold text-destructive">{formatINR(totalOverdue)}</p>
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
                <TableCell className="font-medium">
                  <Link
                    href={ROUTES.INVOICE_DETAIL(invoice.id)}
                    className="hover:underline"
                  >
                    {invoice.invoice_number}
                  </Link>
                </TableCell>
                <TableCell>{invoice.customer_name}</TableCell>
                <TableCell>{formatPhone(invoice.customer_phone ?? "")}</TableCell>
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
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setActionError(null);
                      setReminderTarget(invoice.id);
                    }}
                  >
                    <Send className="mr-1 h-3 w-3" />
                    Remind
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog
        open={!!reminderTarget}
        onOpenChange={(open) => {
          if (!open) setReminderTarget(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send payment reminder</DialogTitle>
            <DialogDescription>
              Review the drafted message before sending on WhatsApp.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Button
                type="button"
                size="sm"
                variant={reminderLanguage === "en" ? "default" : "outline"}
                onClick={() => setReminderLanguage("en")}
              >
                English
              </Button>
              <Button
                type="button"
                size="sm"
                variant={reminderLanguage === "hi" ? "default" : "outline"}
                onClick={() => setReminderLanguage("hi")}
              >
                Hindi
              </Button>
            </div>
            {preview.isLoading && <Skeleton className="h-24 w-full" />}
            {preview.data && (
              <div className="space-y-2 rounded-md border bg-muted/40 p-4 text-sm">
                <p className="font-medium">{preview.data.customer_name}</p>
                <p className="text-muted-foreground">
                  {formatINR(preview.data.amount_due)} · {preview.data.days_overdue} days overdue
                </p>
                <p className="whitespace-pre-wrap">{preview.data.message}</p>
              </div>
            )}
            <Button
              className="w-full"
              disabled={sendReminder.isPending || !reminderTarget}
              onClick={async () => {
                if (!reminderTarget) return;
                setActionError(null);
                try {
                  await sendReminder.mutateAsync(reminderTarget);
                  setReminderTarget(null);
                } catch (err) {
                  setActionError(
                    err instanceof Error ? err.message : "Failed to send reminder",
                  );
                }
              }}
            >
              Send on WhatsApp
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
