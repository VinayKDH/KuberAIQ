"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCaCompliancePack } from "@/features/ca/hooks";
import { CA_WORKSPACE_COPY } from "@/lib/constants";
import { financialYearStartIso, todayIso } from "@/lib/format";

interface CaCompliancePackButtonProps {
  companyId: string;
  companyName: string;
}

export function CaCompliancePackButton({ companyId, companyName }: CaCompliancePackButtonProps) {
  const download = useCaCompliancePack();

  return (
    <Button
      size="sm"
      variant="outline"
      disabled={download.isPending}
      onClick={() =>
        download.mutate({
          companyId,
          companyName,
          from: financialYearStartIso(),
          to: todayIso(),
        })
      }
    >
      <Download className="mr-2 h-4 w-4" />
      {CA_WORKSPACE_COPY.COMPLIANCE_PACK}
    </Button>
  );
}
