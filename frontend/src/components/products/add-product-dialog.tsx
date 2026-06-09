"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useCreateProduct } from "@/features/products/hooks";
import { PRODUCT_FORM } from "@/lib/constants";
import {
  ProductFormFields,
  productFormToPayload,
  type ProductFormValues,
  validateProductForm,
} from "./product-form-fields";

const EMPTY_VALUES: ProductFormValues = {
  name: "",
  description: "",
  hsnSac: "",
  unit: "NOS",
  defaultPrice: "",
  gstRate: "18",
};

export function AddProductDialog() {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<ProductFormValues>(EMPTY_VALUES);
  const [error, setError] = useState<string | null>(null);
  const createProduct = useCreateProduct();

  const reset = () => {
    setValues(EMPTY_VALUES);
    setError(null);
  };

  const handleCreate = async () => {
    setError(null);
    const validationError = validateProductForm(values);
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      await createProduct.mutateAsync(productFormToPayload(values));
      setOpen(false);
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create product");
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (!value) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add product
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{PRODUCT_FORM.TITLE}</DialogTitle>
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

        <Button className="w-full" disabled={createProduct.isPending} onClick={handleCreate}>
          {createProduct.isPending ? "Saving…" : "Create product"}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
