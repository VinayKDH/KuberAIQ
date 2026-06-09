"use client";

import { ComplianceAlertsPreviewPanel } from "@/components/compliance/compliance-alerts-preview";
import { ComplianceDashboardPanel } from "@/components/compliance/compliance-dashboard-panel";
import { COMPLIANCE_COPY } from "@/lib/constants";

export default function CompliancePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">{COMPLIANCE_COPY.TITLE}</h2>
        <p className="text-muted-foreground">{COMPLIANCE_COPY.DESCRIPTION}</p>
      </div>
      <ComplianceAlertsPreviewPanel />
      <ComplianceDashboardPanel />
    </div>
  );
}
