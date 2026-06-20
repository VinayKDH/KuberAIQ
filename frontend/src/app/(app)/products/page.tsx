"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { AddProductDialog } from "@/components/products/add-product-dialog";
import { EditProductDialog } from "@/components/products/edit-product-dialog";
import { LowStockPanel } from "@/components/products/low-stock-panel";
import { StarterProductsBanner } from "@/components/products/starter-products-banner";
import { useDeactivateProduct, useProducts } from "@/features/products/hooks";
import { useDebounce } from "@/hooks/use-debounce";
import { DEFAULT_PAGE_SIZE, PRODUCT_FORM } from "@/lib/constants";
import { formatINR } from "@/lib/format";

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [showInactive, setShowInactive] = useState(false);
  const debouncedSearch = useDebounce(search);
  const { data, isLoading, isError, error } = useProducts({
    q: debouncedSearch || undefined,
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
    active_only: !showInactive,
  });
  const deactivateProduct = useDeactivateProduct();

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Products</h2>
          <p className="text-muted-foreground">Product catalog for invoices and quotations</p>
        </div>
        <AddProductDialog />
      </div>

      <StarterProductsBanner productCount={data?.total ?? 0} />

      <LowStockPanel />

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search products…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="h-4 w-4 rounded border"
          />
          Show inactive
        </label>
      </div>

      {isError && (
        <p className="text-sm text-destructive">
          {error instanceof Error ? error.message : "Failed to load products"}
        </p>
      )}

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>HSN/SAC</TableHead>
              <TableHead>Unit</TableHead>
              <TableHead>GST</TableHead>
              <TableHead className="text-right">Price</TableHead>
              <TableHead>Status</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((__, j) => (
                    <TableCell key={j}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            {!isLoading && data?.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                  No products found
                </TableCell>
              </TableRow>
            )}
            {data?.items.map((product) => (
              <TableRow key={product.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">{product.name}</TableCell>
                <TableCell>{product.hsn_sac ?? "—"}</TableCell>
                <TableCell>{product.unit}</TableCell>
                <TableCell>{product.gst_rate}%</TableCell>
                <TableCell className="text-right">{formatINR(product.default_price)}</TableCell>
                <TableCell>
                  <Badge variant={product.is_active ? "default" : "secondary"}>
                    {product.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    {product.is_active && <EditProductDialog product={product} />}
                    {product.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        disabled={deactivateProduct.isPending}
                        onClick={async () => {
                          if (!window.confirm(PRODUCT_FORM.DEACTIVATE_CONFIRM)) return;
                          await deactivateProduct.mutateAsync(product.id);
                        }}
                      >
                        {PRODUCT_FORM.DEACTIVATE}
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total > 0 && (
        <p className="text-sm text-muted-foreground">
          Showing {data.items.length} of {data.total} products
        </p>
      )}
    </div>
  );
}
