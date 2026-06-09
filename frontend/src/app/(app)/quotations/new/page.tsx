"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { QuotationForm } from "@/components/quotations/quotation-form";
import { useCreateQuotation } from "@/features/quotations/hooks";
import { QUOTATION_COPY, ROUTES } from "@/lib/constants";

export default function NewQuotationPage() {
  const router = useRouter();
  const createQuotation = useCreateQuotation();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={ROUTES.QUOTATIONS}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{QUOTATION_COPY.NEW_TITLE}</h2>
          <p className="text-muted-foreground">Create an estimate for your customer</p>
        </div>
      </div>

      <QuotationForm
        isSubmitting={createQuotation.isPending}
        onSubmit={async (input) => {
          const quotation = await createQuotation.mutateAsync(input);
          router.push(ROUTES.QUOTATION_DETAIL(quotation.id));
        }}
      />
    </div>
  );
}
