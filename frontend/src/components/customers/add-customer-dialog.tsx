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
import { useCreateCustomer } from "@/features/customers/hooks";
import { CUSTOMER_FORM } from "@/lib/constants";
import {
  CustomerFormFields,
  customerFormToPayload,
  type CustomerFormValues,
  validateCustomerForm,
} from "./customer-form-fields";

const EMPTY_VALUES: CustomerFormValues = {
  name: "",
  phone: "",
  email: "",
  gstin: "",
  billingAddress: "",
  notes: "",
};

export function AddCustomerDialog() {
  const [open, setOpen] = useState(false);
  const [values, setValues] = useState<CustomerFormValues>(EMPTY_VALUES);
  const [error, setError] = useState<string | null>(null);
  const [phoneWarning, setPhoneWarning] = useState<string | null>(null);
  const createCustomer = useCreateCustomer();

  const reset = () => {
    setValues(EMPTY_VALUES);
    setError(null);
    setPhoneWarning(null);
  };

  const handleChange = (field: keyof CustomerFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreate = async () => {
    setError(null);
    const validationError = validateCustomerForm(values);
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      await createCustomer.mutateAsync(customerFormToPayload(values));
      setOpen(false);
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create customer");
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
          Add customer
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[90vh] max-w-xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{CUSTOMER_FORM.TITLE}</DialogTitle>
          <DialogDescription>{CUSTOMER_FORM.DESCRIPTION}</DialogDescription>
        </DialogHeader>

        <CustomerFormFields
          values={values}
          onChange={handleChange}
          phoneWarning={phoneWarning}
          onPhoneWarning={setPhoneWarning}
        />

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <Button className="w-full" disabled={createCustomer.isPending} onClick={handleCreate}>
          {createCustomer.isPending ? "Saving…" : "Create customer"}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
