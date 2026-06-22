"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, MessageCircle, Minus, Plus, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCustomers } from "@/features/customers/hooks";
import { useDownloadInvoicePdf, useShareInvoiceWhatsApp } from "@/features/invoices/hooks";
import { useDebounce } from "@/hooks/use-debounce";
import { apiClient, formatApiError } from "@/lib/api-client";
import {
  API_PATHS,
  COUNTER_COPY,
  LOW_STOCK_THRESHOLD,
  QUERY_KEYS,
  ROUTES,
} from "@/lib/constants";
import { formatINR, formatQty } from "@/lib/format";
import { getPreferredLanguage } from "@/lib/i18n";

interface ProductItem {
  id: string;
  name: string;
  default_price: number | string;
  gst_rate: number | string;
  stock_qty: number | string;
  unit: string;
}

interface CounterBillResponse {
  invoice: {
    id: string;
    invoice_number?: string | null;
    grand_total: number | string;
    status: string;
  };
  customer_name: string;
  stock_warning?: string | null;
}

function toNumber(value: number | string): number {
  const num = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(num) ? num : 0;
}

export default function CounterPage() {
  const lang = getPreferredLanguage();
  const copy = COUNTER_COPY;
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const [selected, setSelected] = useState<ProductItem | null>(null);
  const [qty, setQty] = useState(1);
  const [customerName, setCustomerName] = useState("");
  const [customerId, setCustomerId] = useState<string | null>(null);
  const [lastBill, setLastBill] = useState<CounterBillResponse | null>(null);
  const [billError, setBillError] = useState<string | null>(null);
  const [shareMessage, setShareMessage] = useState<string | null>(null);

  const { data: products, isFetching: isSearching } = useQuery({
    queryKey: QUERY_KEYS.PRODUCTS({ q: debouncedQuery }),
    queryFn: () =>
      apiClient<{ items: ProductItem[] }>(API_PATHS.PRODUCTS, {
        params: { q: debouncedQuery, page_size: 8 },
      }),
    enabled: debouncedQuery.length >= 1,
  });

  const { data: customers } = useCustomers({ page_size: 6 });

  const downloadPdf = useDownloadInvoicePdf();
  const shareWhatsApp = useShareInvoiceWhatsApp();

  const billMutation = useMutation({
    mutationFn: () =>
      apiClient<CounterBillResponse>(API_PATHS.INVOICES_COUNTER, {
        method: "POST",
        body: {
          product_id: selected!.id,
          quantity: qty,
          customer_id: customerId ?? undefined,
          customer_name: customerId ? undefined : customerName.trim() || undefined,
        },
      }),
    onSuccess: (data) => {
      setLastBill(data);
      setBillError(null);
      setShareMessage(null);
      setSelected(null);
      setQty(1);
      setQuery("");
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => {
      setBillError(formatApiError(err, copy.ERROR_GENERIC[lang]));
    },
  });

  const lineTotal = useMemo(() => {
    if (!selected) return 0;
    const price = toNumber(selected.default_price);
    const gst = toNumber(selected.gst_rate);
    return price * qty * (1 + gst / 100);
  }, [selected, qty]);

  const showLowStockHint = selected && toNumber(selected.stock_qty) <= LOW_STOCK_THRESHOLD;

  useEffect(() => {
    if (!selected) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Enter" && !billMutation.isPending) {
        event.preventDefault();
        billMutation.mutate();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [selected, billMutation]);

  const handleCustomerPick = (id: string, name: string) => {
    setCustomerId(id);
    setCustomerName(name);
  };

  const handleCustomerNameChange = (value: string) => {
    setCustomerName(value);
    setCustomerId(null);
  };

  const resetForNewBill = () => {
    setLastBill(null);
    setBillError(null);
    setShareMessage(null);
    setQuery("");
    setSelected(null);
    setQty(1);
  };

  return (
    <div className="mx-auto max-w-lg space-y-4 pb-28">
      <div>
        <h2 className="flex items-center gap-2 text-2xl font-bold">
          <ShoppingCart className="h-6 w-6" />
          {copy.TITLE[lang]}
        </h2>
        <p className="text-muted-foreground">{copy.SUBTITLE[lang]}</p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">{copy.SEARCH_PLACEHOLDER[lang]}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={copy.SEARCH_PLACEHOLDER[lang]}
            autoFocus
            inputMode="search"
            autoComplete="off"
          />
          {debouncedQuery.length >= 1 && isSearching ? (
            <p className="text-sm text-muted-foreground">{copy.SEARCHING[lang]}</p>
          ) : null}
          {debouncedQuery.length >= 1 && !isSearching && products?.items?.length === 0 ? (
            <p className="text-sm text-muted-foreground">{copy.NO_RESULTS[lang]}</p>
          ) : null}
          {products?.items?.length ? (
            <ul className="divide-y rounded-md border">
              {products.items.map((product) => (
                <li key={product.id}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between px-3 py-3 text-left hover:bg-muted/50 active:bg-muted"
                    onClick={() => {
                      setSelected(product);
                      setQty(1);
                      setBillError(null);
                    }}
                  >
                    <span className="font-medium">{product.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {formatINR(product.default_price)} · {formatQty(product.stock_qty)}{" "}
                      {product.unit}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>

      {selected && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">{selected.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="counter-customer">{copy.CUSTOMER_LABEL[lang]}</Label>
              <Input
                id="counter-customer"
                value={customerName}
                onChange={(e) => handleCustomerNameChange(e.target.value)}
                placeholder={copy.WALK_IN[lang]}
              />
              {customers?.items?.length ? (
                <div className="flex flex-wrap gap-2">
                  <span className="w-full text-xs text-muted-foreground">
                    {copy.RECENT_CUSTOMERS[lang]}
                  </span>
                  {customers.items.map((customer) => (
                    <Button
                      key={customer.id}
                      type="button"
                      size="sm"
                      variant={customerId === customer.id ? "default" : "outline"}
                      onClick={() => handleCustomerPick(customer.id, customer.name)}
                    >
                      {customer.name}
                    </Button>
                  ))}
                </div>
              ) : null}
            </div>
            <div className="flex items-center justify-between">
              <span>{copy.QTY[lang]}</span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  aria-label="Decrease quantity"
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-8 text-center font-medium">{qty}</span>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  aria-label="Increase quantity"
                  onClick={() => setQty((q) => q + 1)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
            {showLowStockHint ? (
              <p className="text-sm text-amber-600">{copy.STOCK_WARNING[lang]}</p>
            ) : null}
            <p className="text-lg font-semibold">
              {formatINR(lineTotal)}{" "}
              <span className="text-sm font-normal text-muted-foreground">
                ({copy.INCLUDES_GST[lang]})
              </span>
            </p>
            {billError ? <p className="text-sm text-destructive">{billError}</p> : null}
            <Button
              className="w-full"
              size="lg"
              disabled={billMutation.isPending}
              onClick={() => billMutation.mutate()}
            >
              {billMutation.isPending ? copy.BILLING[lang] : copy.BILL_NOW[lang]}
            </Button>
          </CardContent>
        </Card>
      )}

      {lastBill && (
        <Card className="border-green-500/40 bg-green-50/50 dark:bg-green-950/20">
          <CardContent className="space-y-3 pt-6">
            <p className="font-medium">{copy.SUCCESS[lang]}</p>
            <p className="text-sm">
              {lastBill.invoice.invoice_number ?? lastBill.invoice.id.slice(0, 8)} ·{" "}
              {lastBill.customer_name} · {formatINR(lastBill.invoice.grand_total)}
            </p>
            {lastBill.stock_warning ? (
              <p className="text-sm text-amber-700">{lastBill.stock_warning}</p>
            ) : null}
            {shareMessage ? <p className="text-sm text-green-700">{shareMessage}</p> : null}
            <div className="flex flex-wrap gap-2">
              <Link href={ROUTES.INVOICE_DETAIL(lastBill.invoice.id)}>
                <Button variant="outline" size="sm">
                  {copy.VIEW_INVOICE[lang]}
                </Button>
              </Link>
              <Button
                variant="outline"
                size="sm"
                disabled={downloadPdf.isPending}
                onClick={() => downloadPdf.mutate(lastBill.invoice.id)}
              >
                <Download className="mr-1 h-4 w-4" />
                {copy.DOWNLOAD_PDF[lang]}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={shareWhatsApp.isPending}
                onClick={() =>
                  shareWhatsApp.mutate(lastBill.invoice.id, {
                    onSuccess: () => setShareMessage("WhatsApp share queued"),
                    onError: (err) => setShareMessage(formatApiError(err)),
                  })
                }
              >
                <MessageCircle className="mr-1 h-4 w-4" />
                {copy.SHARE_WHATSAPP[lang]}
              </Button>
              <Button variant="ghost" size="sm" onClick={resetForNewBill}>
                {copy.NEW_BILL[lang]}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {selected && (
        <div className="fixed inset-x-0 bottom-0 z-20 border-t bg-background/95 p-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden">
          <Button
            className="w-full"
            size="lg"
            disabled={billMutation.isPending}
            onClick={() => billMutation.mutate()}
          >
            {billMutation.isPending
              ? copy.BILLING[lang]
              : `${copy.BILL_NOW[lang]} · ${formatINR(lineTotal)}`}
          </Button>
        </div>
      )}
    </div>
  );
}
