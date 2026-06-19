"use client";

import { useState } from "react";
import { Repeat } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useCustomers } from "@/features/customers/hooks";
import {
  useCreateRecurringTemplate,
  useRecurringTemplates,
  useUpdateRecurringTemplate,
} from "@/features/invoices/hooks";
import { RECURRING_COPY, RECURRING_INVOICE_FREQUENCIES } from "@/lib/constants";
import { getPreferredLanguage } from "@/lib/i18n";
import { formatDate, todayIso } from "@/lib/format";

export function RecurringTemplatesPanel() {
  const lang = getPreferredLanguage();
  const { data: templates = [], isLoading } = useRecurringTemplates();
  const { data: customers } = useCustomers({ page: 1, page_size: 50 });
  const createMutation = useCreateRecurringTemplate();
  const updateMutation = useUpdateRecurringTemplate();

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [frequency, setFrequency] = useState("MONTHLY");
  const [nextRunDate, setNextRunDate] = useState(todayIso());
  const [amount, setAmount] = useState("1500");
  const [description, setDescription] = useState("Recurring service fee");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const customerOptions = (customers?.items ?? []).map((c) => ({
    value: c.id,
    label: c.name,
  }));

  const handleCreate = async () => {
    setMessage(null);
    setError(null);
    if (!customerId || !name.trim()) {
      setError(RECURRING_COPY.ERROR[lang]);
      return;
    }
    try {
      await createMutation.mutateAsync({
        customer_id: customerId,
        name: name.trim(),
        frequency,
        next_run_date: nextRunDate,
        items: [
          {
            description: description.trim() || "Recurring charge",
            quantity: 1,
            unit: "NOS",
            unit_price: Number(amount) || 0,
            gst_rate: 18,
          },
        ],
      });
      setMessage(RECURRING_COPY.SAVED[lang]);
      setShowForm(false);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : RECURRING_COPY.ERROR[lang]);
    }
  };

  const toggleActive = async (id: string, isActive: boolean) => {
    await updateMutation.mutateAsync({ id, input: { is_active: !isActive } });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">{RECURRING_COPY.TITLE[lang]}</CardTitle>
            <CardDescription>{RECURRING_COPY.DESC[lang]}</CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => setShowForm((v) => !v)}>
            <Repeat className="mr-2 h-4 w-4" />
            {RECURRING_COPY.CREATE[lang]}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {showForm && (
          <div className="space-y-3 rounded-md border p-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label>{RECURRING_COPY.NAME[lang]}</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>{RECURRING_COPY.CUSTOMER[lang]}</Label>
                <Select
                  options={customerOptions}
                  value={customerId}
                  onValueChange={setCustomerId}
                  placeholder={RECURRING_COPY.CUSTOMER[lang]}
                />
              </div>
              <div className="space-y-1">
                <Label>{RECURRING_COPY.FREQUENCY[lang]}</Label>
                <Select
                  options={RECURRING_INVOICE_FREQUENCIES.map((f) => ({
                    value: f.value,
                    label: f.label[lang],
                  }))}
                  value={frequency}
                  onValueChange={setFrequency}
                />
              </div>
              <div className="space-y-1">
                <Label>{RECURRING_COPY.NEXT_RUN[lang]}</Label>
                <Input
                  type="date"
                  value={nextRunDate}
                  min={todayIso()}
                  onChange={(e) => setNextRunDate(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label>{RECURRING_COPY.DESCRIPTION[lang]}</Label>
                <Input value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label>{RECURRING_COPY.AMOUNT[lang]}</Label>
                <Input
                  type="number"
                  min={0}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>
            </div>
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending ? RECURRING_COPY.SAVING[lang] : RECURRING_COPY.SAVE[lang]}
            </Button>
          </div>
        )}

        {error && <p className="text-sm text-destructive">{error}</p>}
        {message && <p className="text-sm text-emerald-600">{message}</p>}

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : templates.length ? (
          <ul className="space-y-2">
            {templates.map((template) => (
              <li
                key={template.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 text-sm"
              >
                <div>
                  <p className="font-medium">{template.name}</p>
                  <p className="text-muted-foreground">
                    {template.frequency} · Next {formatDate(template.next_run_date)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={template.is_active ? "default" : "secondary"}>
                    {template.is_active ? RECURRING_COPY.ACTIVE[lang] : RECURRING_COPY.PAUSED[lang]}
                  </Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={updateMutation.isPending}
                    onClick={() => toggleActive(template.id, template.is_active)}
                  >
                    {template.is_active
                      ? RECURRING_COPY.DISABLE[lang]
                      : RECURRING_COPY.ENABLE[lang]}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">{RECURRING_COPY.EMPTY[lang]}</p>
        )}
      </CardContent>
    </Card>
  );
}
