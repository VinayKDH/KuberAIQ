"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { TopProduct } from "@/features/dashboard/types";
import { formatINR } from "@/lib/format";

interface TopProductsCardProps {
  products: TopProduct[];
}

export function TopProductsCard({ products }: TopProductsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Top products</CardTitle>
        <CardDescription>By line-item revenue in selected period</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-3">
          {products.map((product) => (
            <li key={product.description} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{product.description}</span>
                <span className="text-muted-foreground">{formatINR(product.revenue)}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${Math.min(product.share_pct, 100)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
