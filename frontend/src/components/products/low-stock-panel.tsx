"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api-client";
import { API_PATHS, INVENTORY_COPY, QUERY_KEYS, ROUTES } from "@/lib/constants";

interface ProductItem {
  id: string;
  name: string;
  stock_qty: number;
  unit: string;
}

export function LowStockPanel() {
  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.PRODUCTS_LOW_STOCK,
    queryFn: () => apiClient<{ items: ProductItem[] }>(API_PATHS.PRODUCTS_LOW_STOCK),
  });

  const items = data?.items ?? [];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{INVENTORY_COPY.LOW_STOCK_TITLE}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        {!isLoading && items.length === 0 && (
          <p className="text-sm text-muted-foreground">{INVENTORY_COPY.LOW_STOCK_EMPTY}</p>
        )}
        {!isLoading && items.length > 0 && (
          <ul className="space-y-2 text-sm">
            {items.map((product) => (
              <li key={product.id} className="flex justify-between">
                <Link href={ROUTES.PRODUCTS} className="hover:underline">
                  {product.name}
                </Link>
                <span className="text-destructive">
                  {product.stock_qty} {product.unit}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
