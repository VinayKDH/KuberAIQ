"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useCreateCreditNote } from "@/features/invoices/hooks";
import { CREDIT_NOTE_COPY } from "@/lib/constants";

interface CreditNoteDialogProps {
  invoiceId: string;
}

export function CreditNoteDialog({ invoiceId }: CreditNoteDialogProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const createCreditNote = useCreateCreditNote();

  const reset = () => {
    setReason("");
    setError(null);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        setOpen(value);
        if (!value) reset();
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline">{CREDIT_NOTE_COPY.BUTTON}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{CREDIT_NOTE_COPY.TITLE}</DialogTitle>
          <DialogDescription>{CREDIT_NOTE_COPY.DESCRIPTION}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="credit-reason">{CREDIT_NOTE_COPY.REASON}</Label>
            <Textarea
              id="credit-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={CREDIT_NOTE_COPY.REASON_PLACEHOLDER}
              rows={3}
            />
          </div>
          {error && (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          )}
          <Button
            className="w-full"
            disabled={createCreditNote.isPending || !reason.trim()}
            onClick={async () => {
              setError(null);
              try {
                await createCreditNote.mutateAsync({
                  invoiceId,
                  input: { reason: reason.trim() },
                });
                setOpen(false);
                reset();
              } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to issue credit note");
              }
            }}
          >
            {createCreditNote.isPending ? "Issuing…" : CREDIT_NOTE_COPY.SUBMIT}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
