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
import { useUpdateCustomer } from "@/features/customers/hooks";
import type { Customer } from "@/features/customers/types";
import { CUSTOMER_FORM } from "@/lib/constants";
import {
  CustomerFormFields,
  customerFormToPayload,
  customerToFormValues,
  type CustomerFormValues,
  validateCustomerForm,
} from "./customer-form-fields";

interface EditCustomerDialogProps {
  customer: Customer;
}

export function EditCustomerDialog({ customer }: EditCustomerDialogProps) {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<CustomerFormValues>(() => customerToFormValues(customer));
  const [error, setError] = useState<string | null>(null);
  const [phoneWarning, setPhoneWarning] = useState<string | null>(null);
  const updateCustomer = useUpdateCustomer(customer.id);

  useEffect(() => {
    if (open) {
      setValues(customerToFormValues(customer));
      setError(null);
      setPhoneWarning(null);
    }
  }, [open, customer]);

  const handleChange = (field: keyof CustomerFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setError(null);
    const validationError = validateCustomerForm(values);
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      await updateCustomer.mutateAsync(customerFormToPayload(values));
      setOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update customer");
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
          <DialogTitle>{CUSTOMER_FORM.EDIT_TITLE}</DialogTitle>
          <DialogDescription>{CUSTOMER_FORM.DESCRIPTION}</DialogDescription>
        </DialogHeader>

        <CustomerFormFields
          values={values}
          onChange={handleChange}
          phoneWarning={phoneWarning}
          onPhoneWarning={setPhoneWarning}
          excludeCustomerId={customer.id}
          idPrefix="edit"
        />

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <Button className="w-full" disabled={updateCustomer.isPending} onClick={handleSave}>
          {updateCustomer.isPending ? "Saving…" : "Save changes"}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
