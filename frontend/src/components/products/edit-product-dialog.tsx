"use client";

import { useEffect, useState } from "react";
import { Pencil } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useUpdateProduct } from "@/features/products/hooks";
import type { Product } from "@/features/products/types";
import { PRODUCT_FORM } from "@/lib/constants";
import {
  ProductFormFields,
  productFormToPayload,
  productToFormValues,
  type ProductFormValues,
  validateProductForm,
} from "./product-form-fields";

interface EditProductDialogProps {
  product: Product;
}

export function EditProductDialog({ product }: EditProductDialogProps) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<ProductFormValues>(() => productToFormValues(product));
  const [error, setError] = useState<string | null>(null);
  const updateProduct = useUpdateProduct();

  useEffect(() => {
    if (open) {
      setValues(productToFormValues(product));
      setError(null);
    }
  }, [open, product]);

  const handleSave = async () => {
    setError(null);
    const validationError = validateProductForm(values);
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      await updateProduct.mutateAsync({ id: product.id, input: productFormToPayload(values) });
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update product");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Pencil className="mr-2 h-4 w-4" />
          Edit
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{PRODUCT_FORM.EDIT_TITLE}</DialogTitle>
          <DialogDescription>{PRODUCT_FORM.DESCRIPTION}</DialogDescription>
        </DialogHeader>

        <ProductFormFields
          values={values}
          onChange={(field, value) => setValues((prev) => ({ ...prev, [field]: value }))}
        />

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <Button className="w-full" disabled={updateProduct.isPending} onClick={handleSave}>
          {updateProduct.isPending ? "Saving…" : "Save changes"}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
