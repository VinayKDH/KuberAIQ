"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ROUTES } from "@/lib/constants";

export default function NewInvoicePage() {
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
      <Card>
        <CardHeader>
          <CardTitle>Coming soon</CardTitle>
          <CardDescription>
            Invoice creation form will be connected to the backend API
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href={ROUTES.INVOICES}>
            <Button variant="outline">Back to invoices</Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
