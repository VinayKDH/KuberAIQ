"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api-client";
import { API_PATHS } from "@/lib/constants";
import { formatDate, formatINR, todayIso } from "@/lib/format";

interface Expense {
  id: string;
  expense_date: string;
  category: string;
  amount: number | string;
  vendor_name?: string | null;
  note?: string | null;
}

export default function ExpensesPage() {
  const queryClient = useQueryClient();
  const [expenseDate, setExpenseDate] = useState(todayIso());
  const [category, setCategory] = useState("General");
  const [amount, setAmount] = useState("");
  const [vendorName, setVendorName] = useState("");
  const [note, setNote] = useState("");
  const { data } = useQuery({
    queryKey: ["expenses"],
    queryFn: () => apiClient<{ items: Expense[] }>(API_PATHS.EXPENSES),
  });
  const create = useMutation({
    mutationFn: () =>
      apiClient(API_PATHS.EXPENSES, {
        method: "POST",
        body: {
          expense_date: expenseDate,
          category,
          amount: Number(amount),
          vendor_name: vendorName || null,
          note: note || null,
        },
      }),
    onSuccess: () => {
      setAmount("");
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Expenses</h2>
        <p className="text-muted-foreground">Track daily business expenses.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add expense</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-5">
          <div className="space-y-1">
            <Label>Date</Label>
            <Input type="date" value={expenseDate} onChange={(e) => setExpenseDate(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>Category</Label>
            <Input value={category} onChange={(e) => setCategory(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>Amount</Label>
            <Input value={amount} onChange={(e) => setAmount(e.target.value)} type="number" min="0" />
          </div>
          <div className="space-y-1">
            <Label>Vendor</Label>
            <Input value={vendorName} onChange={(e) => setVendorName(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label>Note</Label>
            <Input value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          <Button
            className="md:col-span-5 justify-self-start"
            disabled={create.isPending || !amount}
            onClick={() => create.mutate()}
          >
            Add expense
          </Button>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent expenses</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {data?.items?.map((row) => (
            <div key={row.id} className="flex items-center justify-between rounded border p-2 text-sm">
              <div>
                <p className="font-medium">{row.category}</p>
                <p className="text-muted-foreground">
                  {formatDate(row.expense_date)} · {row.vendor_name ?? "—"}
                </p>
              </div>
              <p>{formatINR(row.amount)}</p>
            </div>
          ))}
          {!data?.items?.length && <p className="text-sm text-muted-foreground">No expenses added yet.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
