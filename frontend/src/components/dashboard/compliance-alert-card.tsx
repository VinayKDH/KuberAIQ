"use client";

import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { ROUTES } from "@/lib/constants";
import type { ComplianceAlert } from "@/features/compliance/types";

interface ComplianceAlertCardProps {
  alert?: ComplianceAlert | null;
}

export function ComplianceAlertCard({ alert }: ComplianceAlertCardProps) {
  if (!alert?.triggered) {
    return null;
  }

  return (
    <Card className="border-amber-500/50 bg-amber-50/50 dark:bg-amber-950/20">
      <CardContent className="flex items-start gap-3 pt-6">
        <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-600" />
        <div className="space-y-1">
          <p className="font-medium text-amber-900 dark:text-amber-100">Compliance alert</p>
          <p className="text-sm text-amber-800 dark:text-amber-200">{alert.message}</p>
          <Link href={ROUTES.COMPLIANCE} className="text-sm font-medium underline">
            Open Compliance Center
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
