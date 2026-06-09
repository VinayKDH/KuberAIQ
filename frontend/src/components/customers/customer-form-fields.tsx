"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api-client";
import { API_PATHS, CUSTOMER_FORM } from "@/lib/constants";

export interface CustomerFormValues {
  name: string;
  phone: string;
  email: string;
  gstin: string;
  billingAddress: string;
  notes: string;
}

interface CustomerFormFieldsProps {
  values: CustomerFormValues;
  onChange: (field: keyof CustomerFormValues, value: string) => void;
  phoneWarning: string | null;
  onPhoneWarning: (warning: string | null) => void;
  excludeCustomerId?: string;
  idPrefix?: string;
}

export function CustomerFormFields({
  values,
  onChange,
  phoneWarning,
  onPhoneWarning,
  excludeCustomerId,
  idPrefix = "",
}: CustomerFormFieldsProps) {
  const fieldId = (name: string) => (idPrefix ? `${idPrefix}-${name}` : name);

  return (
    <div className="space-y-6">
      <section className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground">
          {CUSTOMER_FORM.SECTION_BUSINESS}
        </h3>
        <div className="space-y-2">
          <Label htmlFor={fieldId("company-name")}>{CUSTOMER_FORM.COMPANY_NAME}</Label>
          <Input
            id={fieldId("company-name")}
            value={values.name}
            onChange={(e) => onChange("name", e.target.value)}
            placeholder="ABC Traders Pvt Ltd"
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={fieldId("gstin")}>{CUSTOMER_FORM.GSTIN}</Label>
          <Input
            id={fieldId("gstin")}
            value={values.gstin}
            onChange={(e) => onChange("gstin", e.target.value.toUpperCase())}
            placeholder="27ABCDE1234F1Z5"
            maxLength={15}
          />
          <p className="text-xs text-muted-foreground">{CUSTOMER_FORM.GSTIN_HINT}</p>
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground">
          {CUSTOMER_FORM.SECTION_CONTACT}
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor={fieldId("phone")}>{CUSTOMER_FORM.PHONE}</Label>
            <Input
              id={fieldId("phone")}
              value={values.phone}
              onChange={(e) => {
                onChange("phone", e.target.value);
                onPhoneWarning(null);
              }}
              onBlur={async () => {
                if (values.phone.trim().length < 10) return;
                try {
                  const result = await apiClient<{ exists: boolean; customer_id?: string }>(
                    API_PATHS.CUSTOMERS_CHECK_PHONE,
                    { params: { phone: values.phone.trim() } },
                  );
                  if (
                    result.exists &&
                    (!excludeCustomerId || result.customer_id !== excludeCustomerId)
                  ) {
                    onPhoneWarning("A customer with this phone number already exists.");
                  }
                } catch {
                  onPhoneWarning(null);
                }
              }}
              placeholder="9876543210"
              required
            />
            {phoneWarning && <p className="text-sm text-amber-600">{phoneWarning}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor={fieldId("email")}>{CUSTOMER_FORM.EMAIL}</Label>
            <Input
              id={fieldId("email")}
              type="email"
              value={values.email}
              onChange={(e) => onChange("email", e.target.value)}
              placeholder="billing@customer.com"
            />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground">
          {CUSTOMER_FORM.SECTION_BILLING}
        </h3>
        <div className="space-y-2">
          <Label htmlFor={fieldId("address")}>{CUSTOMER_FORM.ADDRESS}</Label>
          <Textarea
            id={fieldId("address")}
            value={values.billingAddress}
            onChange={(e) => onChange("billingAddress", e.target.value)}
            placeholder="Shop 12, MIDC Industrial Area, Pune, Maharashtra 411019"
            rows={3}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={fieldId("notes")}>{CUSTOMER_FORM.NOTES}</Label>
          <Textarea
            id={fieldId("notes")}
            value={values.notes}
            onChange={(e) => onChange("notes", e.target.value)}
            placeholder="Payment terms, delivery notes, etc."
            rows={2}
          />
        </div>
      </section>
    </div>
  );
}

export function validateCustomerForm(values: CustomerFormValues): string | null {
  if (!values.name.trim()) return "Company name is required";
  if (!values.phone.trim()) return "Mobile number is required";
  if (!values.billingAddress.trim()) return "Billing address is required for invoices";
  return null;
}

export function customerFormToPayload(values: CustomerFormValues) {
  return {
    name: values.name.trim(),
    phone: values.phone.trim(),
    email: values.email.trim() || undefined,
    gstin: values.gstin.trim() || undefined,
    billing_address: values.billingAddress.trim(),
    notes: values.notes.trim() || undefined,
  };
}

export function customerToFormValues(customer: {
  name: string;
  phone: string;
  email?: string | null;
  gstin?: string | null;
  billing_address?: string | null;
  notes?: string | null;
}): CustomerFormValues {
  return {
    name: customer.name,
    phone: customer.phone,
    email: customer.email ?? "",
    gstin: customer.gstin ?? "",
    billingAddress: customer.billing_address ?? "",
    notes: customer.notes ?? "",
  };
}
