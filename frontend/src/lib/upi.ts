/** Build a UPI deep-link for mobile payment apps. */
export function buildUpiPayUrl(params: {
  vpa: string;
  payeeName?: string;
  amount: number;
  note?: string;
}): string {
  const search = new URLSearchParams();
  search.set("pa", params.vpa.trim());
  if (params.payeeName?.trim()) {
    search.set("pn", params.payeeName.trim());
  }
  search.set("am", params.amount.toFixed(2));
  search.set("cu", "INR");
  if (params.note?.trim()) {
    search.set("tn", params.note.trim().slice(0, 80));
  }
  return `upi://pay?${search.toString()}`;
}
