"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useUpdateComplianceProfile } from "@/features/compliance/hooks";
import type { ComplianceProfile } from "@/features/compliance/types";
import {
  COMPLIANCE_COPY,
  COMPLIANCE_ENTITY_TYPES,
  COMPLIANCE_GSTR1_FREQUENCIES,
  COMPLIANCE_TURNOVER_BANDS,
} from "@/lib/constants";

interface ComplianceProfileSettingsProps {
  profile: ComplianceProfile;
}

export function ComplianceProfileSettings({ profile }: ComplianceProfileSettingsProps) {
  const mutation = useUpdateComplianceProfile();
  const [entityType, setEntityType] = useState(profile.entity_type ?? "PROPRIETORSHIP");
  const [turnoverBand, setTurnoverBand] = useState(profile.turnover_band ?? "");
  const [gstr1Frequency, setGstr1Frequency] = useState(profile.gstr1_filing_frequency ?? "MONTHLY");
  const [employeeCount, setEmployeeCount] = useState(String(profile.employee_count ?? ""));
  const [udyamNumber, setUdyamNumber] = useState(profile.udyam_number ?? "");
  const [hasTds, setHasTds] = useState(profile.has_tds_applicable ?? false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setEntityType(profile.entity_type ?? "PROPRIETORSHIP");
    setTurnoverBand(profile.turnover_band ?? "");
    setGstr1Frequency(profile.gstr1_filing_frequency ?? "MONTHLY");
    setEmployeeCount(String(profile.employee_count ?? ""));
    setUdyamNumber(profile.udyam_number ?? "");
    setHasTds(profile.has_tds_applicable ?? false);
  }, [profile]);

  const save = async () => {
    setMessage(null);
    try {
      await mutation.mutateAsync({
        entity_type: entityType,
        turnover_band: turnoverBand || undefined,
        gstr1_filing_frequency: gstr1Frequency,
        employee_count: employeeCount ? Number(employeeCount) : undefined,
        udyam_number: udyamNumber || undefined,
        has_tds_applicable: hasTds,
      });
      setMessage("Compliance profile saved.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Save failed");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{COMPLIANCE_COPY.PROFILE_TITLE}</CardTitle>
        <CardDescription>{COMPLIANCE_COPY.PROFILE_HINT}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Entity type</Label>
            <Select
              value={entityType}
              options={COMPLIANCE_ENTITY_TYPES.map((item) => ({ value: item.value, label: item.label }))}
              onValueChange={setEntityType}
            />
          </div>
          <div className="space-y-2">
            <Label>Annual turnover band</Label>
            <Select
              value={turnoverBand}
              placeholder="Select turnover band"
              options={COMPLIANCE_TURNOVER_BANDS.map((item) => ({ value: item.value, label: item.label }))}
              onValueChange={setTurnoverBand}
            />
          </div>
          <div className="space-y-2">
            <Label>GSTR-1 filing frequency</Label>
            <Select
              value={gstr1Frequency}
              options={COMPLIANCE_GSTR1_FREQUENCIES.map((item) => ({ value: item.value, label: item.label }))}
              onValueChange={setGstr1Frequency}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="employee-count">Employee count</Label>
            <Input
              id="employee-count"
              type="number"
              min={0}
              value={employeeCount}
              onChange={(e) => setEmployeeCount(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="udyam">Udyam registration number</Label>
            <Input id="udyam" value={udyamNumber} onChange={(e) => setUdyamNumber(e.target.value)} />
          </div>
          <div className="flex items-center gap-3 rounded-md border p-3">
            <input
              id="tds"
              type="checkbox"
              checked={hasTds}
              onChange={(e) => setHasTds(e.target.checked)}
              className="h-4 w-4"
            />
            <div>
              <Label htmlFor="tds">TDS applicable</Label>
              <p className="text-xs text-muted-foreground">Enable if you deduct tax at source on payments</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={save} disabled={mutation.isPending}>
            {COMPLIANCE_COPY.SAVE_PROFILE}
          </Button>
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
