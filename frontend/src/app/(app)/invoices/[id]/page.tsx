"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, Download, MessageCircle } from "lucide-react";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { Textarea } from "@/components/ui/textarea";
import { GstSummary } from "@/components/invoices/gst-summary";
import { CreditNoteDialog } from "@/components/invoices/credit-note-dialog";
import { InvoiceIrnPanel } from "@/components/invoices/invoice-irn-panel";
import {
  useCancelInvoice,
  useCreditNotes,
  useDownloadInvoicePdf,
  useInvoice,
  useInvoicePayments,
  useIssueInvoice,
  useRecordPayment,
  useReversePayment,
  useShareInvoiceWhatsApp,
} from "@/features/invoices/hooks";
import {
  CREDIT_NOTE_COPY,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_VARIANTS,
  PAYMENT_METHOD_LABELS,
  PAYMENT_METHODS,
  ROUTES,
} from "@/lib/constants";
import { formatDate, formatINR, todayIso } from "@/lib/format";

export default function InvoiceDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const { data: invoice, isLoading, isError, error } = useInvoice(id);
  const { data: payments } = useInvoicePayments(id);
  const issueInvoice = useIssueInvoice();
  const cancelInvoice = useCancelInvoice();
  const recordPayment = useRecordPayment();
  const downloadPdf = useDownloadInvoicePdf();
  const shareWhatsApp = useShareInvoiceWhatsApp();
  const reversePayment = useReversePayment();
  const { data: creditNotes } = useCreditNotes(id);

  const [paymentOpen, setPaymentOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [shareSuccess, setShareSuccess] = useState<string | null>(null);
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("UPI");
  const [paymentDate, setPaymentDate] = useState(todayIso());
  const [cancelReason, setCancelReason] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (isError || !invoice) {
    return (
      <p className="text-destructive">
        {error instanceof Error ? error.message : "Invoice not found"}
      </p>
    );
  }

  const canIssue = invoice.status === "DRAFT";
  const canPay = ["ISSUED", "PARTIALLY_PAID", "OVERDUE"].includes(invoice.status);
  const canCancel = !["PAID", "CANCELLED"].includes(invoice.status);
  const canCredit = ["ISSUED", "PARTIALLY_PAID", "OVERDUE"].includes(invoice.status);
  const canShare = !["DRAFT", "CANCELLED"].includes(invoice.status);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-4">
          <Link href={ROUTES.INVOICES}>
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-2xl font-bold tracking-tight">
                {invoice.invoice_number ?? "Draft invoice"}
              </h2>
              <Badge variant={INVOICE_STATUS_VARIANTS[invoice.status] ?? "secondary"}>
                {INVOICE_STATUS_LABELS[invoice.status] ?? invoice.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {invoice.customer?.name ?? "Customer"} · Issued {formatDate(invoice.issue_date)} · Due{" "}
              {formatDate(invoice.due_date)}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {canShare && (
            <>
              <Button
                variant="outline"
                disabled={downloadPdf.isPending}
                onClick={async () => {
                  setActionError(null);
                  setShareSuccess(null);
                  try {
                    await downloadPdf.mutateAsync(id);
                  } catch (err) {
                    setActionError(err instanceof Error ? err.message : "PDF download failed");
                  }
                }}
              >
                <Download className="mr-1 h-4 w-4" />
                Download PDF
              </Button>
              <Button
                variant="outline"
                disabled={shareWhatsApp.isPending}
                onClick={async () => {
                  setActionError(null);
                  setShareSuccess(null);
                  try {
                    const result = await shareWhatsApp.mutateAsync(id);
                    setShareSuccess(result.provider_message_id ?? "Sent via WhatsApp");
                  } catch (err) {
                    setActionError(err instanceof Error ? err.message : "WhatsApp share failed");
                  }
                }}
              >
                <MessageCircle className="mr-1 h-4 w-4" />
                Share on WhatsApp
              </Button>
            </>
          )}
          {canIssue && (
            <Button
              onClick={async () => {
                setActionError(null);
                try {
                  await issueInvoice.mutateAsync(id);
                } catch (err) {
                  setActionError(err instanceof Error ? err.message : "Failed to issue");
                }
              }}
              disabled={issueInvoice.isPending}
            >
              Issue invoice
            </Button>
          )}
          {canPay && (
            <Dialog open={paymentOpen} onOpenChange={setPaymentOpen}>
              <DialogTrigger asChild>
                <Button variant="outline">Record payment</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Record payment</DialogTitle>
                  <DialogDescription>
                    Outstanding: {formatINR(invoice.amount_due)}
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="amount">Amount (₹)</Label>
                    <Input
                      id="amount"
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={paymentAmount}
                      onChange={(e) => setPaymentAmount(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="method">Method</Label>
                    <Select
                      id="method"
                      options={PAYMENT_METHODS.map((m) => ({
                        value: m.value,
                        label: m.label,
                      }))}
                      value={paymentMethod}
                      onValueChange={setPaymentMethod}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="paid_on">Paid on</Label>
                    <Input
                      id="paid_on"
                      type="date"
                      value={paymentDate}
                      onChange={(e) => setPaymentDate(e.target.value)}
                    />
                  </div>
                  <Button
                    className="w-full"
                    disabled={recordPayment.isPending}
                    onClick={async () => {
                      setActionError(null);
                      try {
                        await recordPayment.mutateAsync({
                          invoiceId: id,
                          input: {
                            amount: Number(paymentAmount),
                            paid_on: paymentDate,
                            method: paymentMethod,
                          },
                        });
                        setPaymentOpen(false);
                        setPaymentAmount("");
                      } catch (err) {
                        setActionError(err instanceof Error ? err.message : "Payment failed");
                      }
                    }}
                  >
                    Save payment
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
          {canCredit && <CreditNoteDialog invoiceId={id} />}
          {canCancel && (
            <Dialog open={cancelOpen} onOpenChange={setCancelOpen}>
              <DialogTrigger asChild>
                <Button variant="destructive">Cancel invoice</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Cancel invoice</DialogTitle>
                  <DialogDescription>This action cannot be undone.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reason">Reason</Label>
                    <Textarea
                      id="reason"
                      value={cancelReason}
                      onChange={(e) => setCancelReason(e.target.value)}
                      placeholder="Why is this invoice being cancelled?"
                    />
                  </div>
                  <Button
                    variant="destructive"
                    className="w-full"
                    disabled={cancelInvoice.isPending || !cancelReason.trim()}
                    onClick={async () => {
                      setActionError(null);
                      try {
                        await cancelInvoice.mutateAsync({ id, reason: cancelReason.trim() });
                        setCancelOpen(false);
                      } catch (err) {
                        setActionError(err instanceof Error ? err.message : "Cancel failed");
                      }
                    }}
                  >
                    Confirm cancel
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {actionError && (
        <p className="text-sm text-destructive" role="alert">
          {actionError}
        </p>
      )}

      {shareSuccess && (
        <p className="text-sm text-green-600 dark:text-green-400" role="status">
          WhatsApp message sent ({shareSuccess})
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Line items</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Qty</TableHead>
                  <TableHead>Rate</TableHead>
                  <TableHead>GST</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(invoice.items ?? []).map((item) => (
                  <TableRow key={item.line_no}>
                    <TableCell>{item.line_no}</TableCell>
                    <TableCell>{item.description}</TableCell>
                    <TableCell>
                      {item.quantity} {item.unit}
                    </TableCell>
                    <TableCell>{formatINR(item.unit_price)}</TableCell>
                    <TableCell>{item.gst_rate}%</TableCell>
                    <TableCell className="text-right">{formatINR(item.line_total)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <GstSummary invoice={invoice} />
          <InvoiceIrnPanel invoice={invoice} />
        </div>
      </div>

      {(creditNotes?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{CREDIT_NOTE_COPY.LIST_TITLE}</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Credit note #</TableHead>
                  <TableHead>Issue date</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {creditNotes?.map((note) => (
                  <TableRow key={note.id}>
                    <TableCell>{note.invoice_number ?? note.id.slice(0, 8)}</TableCell>
                    <TableCell>{formatDate(note.issue_date)}</TableCell>
                    <TableCell>{note.credit_reason ?? "—"}</TableCell>
                    <TableCell className="text-right">{formatINR(note.grand_total)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {(payments?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Payments</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Reference</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead />
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments?.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell>{formatDate(payment.paid_on)}</TableCell>
                    <TableCell>
                      {PAYMENT_METHOD_LABELS[payment.method] ?? payment.method}
                    </TableCell>
                    <TableCell>{payment.reference ?? "—"}</TableCell>
                    <TableCell className="text-right">{formatINR(payment.amount)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={reversePayment.isPending}
                        onClick={async () => {
                          setActionError(null);
                          try {
                            await reversePayment.mutateAsync({
                              invoiceId: id,
                              paymentId: payment.id,
                            });
                          } catch (err) {
                            setActionError(
                              err instanceof Error ? err.message : "Failed to reverse payment",
                            );
                          }
                        }}
                      >
                        Reverse
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {creditNotes && creditNotes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Credit notes</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Number</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {creditNotes.map((note) => (
                  <TableRow key={note.id}>
                    <TableCell>{note.invoice_number}</TableCell>
                    <TableCell>{formatDate(note.issue_date)}</TableCell>
                    <TableCell>{note.credit_reason ?? "—"}</TableCell>
                    <TableCell className="text-right">{formatINR(note.grand_total)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
