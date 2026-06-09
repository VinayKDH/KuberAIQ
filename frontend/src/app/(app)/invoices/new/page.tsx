"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { InvoiceForm } from "@/components/invoices/invoice-form";
import { useCreateInvoice } from "@/features/invoices/hooks";
import { ROUTES } from "@/lib/constants";

export default function NewInvoicePage() {
  const router = useRouter();
  const createInvoice = useCreateInvoice();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={ROUTES.INVOICES}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">New Invoice</h2>
          <p className="text-muted-foreground">Create a GST-compliant invoice</p>
        </div>
      </div>

      <InvoiceForm
        isSubmitting={createInvoice.isPending}
        onSubmit={async (input) => {
          const invoice = await createInvoice.mutateAsync(input);
          router.push(ROUTES.INVOICE_DETAIL(invoice.id));
        }}
      />
    </div>
  );
}
