"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Minus, Plus, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api-client";
import {
  API_PATHS,
  COUNTER_COPY,
  QUERY_KEYS,
  ROUTES,
} from "@/lib/constants";
import { formatINR } from "@/lib/format";
import { getPreferredLanguage } from "@/lib/i18n";
import { useDebounce } from "@/hooks/use-debounce";

interface ProductItem {
  id: string;
  name: string;
  default_price: number;
  gst_rate: number;
  stock_qty: number;
  unit: string;
}

interface CounterBillResponse {
  invoice: { id: string; invoice_number?: string | null; grand_total: number };
  customer_name: string;
  stock_warning?: string | null;
}

export default function CounterPage() {
  const lang = getPreferredLanguage();
  const copy = COUNTER_COPY;
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const [selected, setSelected] = useState<ProductItem | null>(null);
  const [qty, setQty] = useState(1);
  const [customerName, setCustomerName] = useState("");
  const [lastBill, setLastBill] = useState<CounterBillResponse | null>(null);

  const { data: products } = useQuery({
    queryKey: QUERY_KEYS.PRODUCTS({ q: debouncedQuery }),
    queryFn: () =>
      apiClient<{ items: ProductItem[] }>(API_PATHS.PRODUCTS, {
        params: { q: debouncedQuery, page_size: 8 },
      }),
    enabled: debouncedQuery.length >= 1,
  });

  const billMutation = useMutation({
    mutationFn: () =>
      apiClient<CounterBillResponse>(API_PATHS.INVOICES_COUNTER, {
        method: "POST",
        body: {
          product_id: selected!.id,
          quantity: String(qty),
          customer_name: customerName.trim() || undefined,
        },
      }),
    onSuccess: (data) => {
      setLastBill(data);
      setSelected(null);
      setQty(1);
      setQuery("");
    },
  });

  const lineTotal = useMemo(() => {
    if (!selected) return 0;
    return Number(selected.default_price) * qty * (1 + Number(selected.gst_rate) / 100);
  }, [selected, qty]);

  return (
    <div className="mx-auto max-w-lg space-y-4 pb-24">
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
          />
          {products?.items?.length ? (
            <ul className="divide-y rounded-md border">
              {products.items.map((product) => (
                <li key={product.id}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-muted/50"
                    onClick={() => {
                      setSelected(product);
                      setQty(1);
                    }}
                  >
                    <span>{product.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {formatINR(product.default_price)} · {product.stock_qty} {product.unit}
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
            <div className="space-y-1">
              <Label>{copy.CUSTOMER_LABEL[lang]}</Label>
              <Input
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder={copy.WALK_IN[lang]}
              />
            </div>
            <div className="flex items-center justify-between">
              <span>{copy.QTY[lang]}</span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={() => setQty((q) => Math.max(1, q - 1))}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className="w-8 text-center font-medium">{qty}</span>
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={() => setQty((q) => q + 1)}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
            {selected.stock_qty <= 10 && (
              <p className="text-sm text-amber-600">{copy.STOCK_WARNING[lang]}</p>
            )}
            <p className="text-lg font-semibold">{formatINR(lineTotal)}</p>
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
          <CardContent className="space-y-2 pt-6">
            <p className="font-medium">{copy.SUCCESS[lang]}</p>
            <p className="text-sm">
              {lastBill.invoice.invoice_number} · {lastBill.customer_name} ·{" "}
              {formatINR(lastBill.invoice.grand_total)}
            </p>
            {lastBill.stock_warning && (
              <p className="text-sm text-amber-700">{lastBill.stock_warning}</p>
            )}
            <Link href={ROUTES.INVOICE_DETAIL(lastBill.invoice.id)}>
              <Button variant="outline" size="sm">
                View invoice
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
