# 13. UI Wireframes

Low-fidelity ASCII wireframes for the seven Phase-1 pages. Design language: clean
enterprise SaaS, shadcn/ui components, light/dark mode, mobile-responsive (sidebar
collapses to a bottom nav / sheet on small screens). Currency INR, dates IST.

## 13.1 Design tokens

- **Primary:** Indigo 600 (`#4f46e5`). **Accent/success:** Emerald. **Warning:** Amber. **Danger:** Rose.
- **Radius:** `rounded-2xl` cards, `rounded-lg` inputs. **Shadow:** soft `shadow-sm`.
- **Font:** Inter. **Spacing:** 4px scale. **Charts:** recharts, muted grid, brand series.

## 13.2 Login

```
┌───────────────────────────────────────────────┐
│                                                 │
│                ▢  VyaparAI                       │
│        AI Business Manager for MSMEs            │
│                                                 │
│   ┌─────────────────────────────────────────┐  │
│   │   [  Sign in with Microsoft  ]           │  │
│   └─────────────────────────────────────────┘  │
│                                                 │
│   By continuing you agree to Terms & Privacy.   │
└───────────────────────────────────────────────┘
```

## 13.3 App shell (all authenticated pages)

```
┌──────────┬──────────────────────────────────────────────┐
│ VyaparAI │  Dashboard         [search]   🔔  🌗  Ramesh ▾ │
│          ├──────────────────────────────────────────────┤
│ ▣ Dash   │                                              │
│ ⬚ Invoices│              < page content >                │
│ ⬚ Customers                                              │
│ ⬚ Collect │                                              │
│ ✦ Assistant                                              │
│ ⚙ Settings│                                              │
│          │                                              │
│  [+ New] │                                              │
└──────────┴──────────────────────────────────────────────┘
```

## 13.4 Dashboard

```
┌───────────────── Dashboard ──────────────  [This FY ▾] ┐
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│ │ Revenue │ │ Pending │ │ Overdue │ │Customers│        │
│ │ ₹8.45L  │ │ ₹2.30L  │ │ ₹0.92L  │ │   48    │        │
│ │  ▲ 12%  │ │  13 inv │ │  ⚠ 5    │ │  ▲ 4    │        │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│ ┌───────────────── Revenue trend ────────────────────┐ │
│ │  ╭─╮      ╭──╮     ╭───╮                            │ │
│ │ ─╯ ╰──╮ ╭─╯  ╰─────╯   ╰──  (line chart)            │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌──── Aging report ────┐ ┌──── Cash flow (expected) ──┐ │
│ │ 0-30   ██████  ₹1.2L │ │ Jul ████████  ₹1.8L        │ │
│ │ 31-60  ███     ₹0.7L │ │ Aug ████      ₹0.95L       │ │
│ │ 61-90  █       ₹0.25L│ │ Sep ██        ₹0.4L        │ │
│ │ 90+    █       ₹0.15L│ │ * expected, not guaranteed │ │
│ └──────────────────────┘ └────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 13.5 Invoices (list)

```
┌──────── Invoices ───────────── [+ New invoice] ── [⌕ search] ┐
│ Filters: [Status ▾] [Customer ▾] [From] [To]      [Export]  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Number            Customer     Date       Total   Status │ │
│ │ INV/2025-26/0042  ABC Traders  06 Jun  ₹20,650  ● Issued │ │
│ │ INV/2025-26/0041  Raj Traders  04 Jun  ₹12,300  ● Paid   │ │
│ │ INV/2025-26/0040  Sham & Co    28 May  ₹ 8,900  ⚠ Overdue│ │
│ │ ...                                                       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                              < 1 2 3 ... >    20 / page      │
└─────────────────────────────────────────────────────────────┘
```

## 13.6 Invoice — create / view

```
┌──────── New invoice ───────────────────────────────────────┐
│ Customer  [ ABC Traders            ▾ ]   Issue [06 Jun 2026]│
│                                          Due   [21 Jun 2026]│
│ ┌── Items ───────────────────────────────────────────────┐ │
│ │ Description     HSN   Qty  Unit  Rate    GST%   Amount  │ │
│ │ [Cement OPC53] [2523][50][BAG ][350.00][18 ▾] ₹17,500  │ │
│ │ [+ Add line]                                            │ │
│ └─────────────────────────────────────────────────────────┘│
│                     Taxable ₹17,500  CGST ₹1,575           │
│                     SGST ₹1,575      Total ₹20,650         │
│ [ Save draft ]      [ Issue invoice ]   [ Issue & WhatsApp ]│
└─────────────────────────────────────────────────────────────┘
```

## 13.7 Customers

```
┌──────── Customers ──────────── [+ New] ────── [⌕ name/phone] ┐
│ Name          Phone        GSTIN            Outstanding      │
│ ABC Traders   98765 43210  27ABCDE1234F1Z5  ₹20,650   [→]   │
│ Raj Traders   90000 11111  27RAJXX....       ₹0        [→]   │
│ ...                                                          │
└─────────────────────────────────────────────────────────────┘
  (detail page → profile, invoices tab, payments tab, aging)
```

## 13.8 Collections

```
┌──────── Collections ─────────────  [Send reminders to all ▸] ┐
│ Overdue: 12 invoices · ₹2,30,000                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Customer    Invoice   Due      Days  Amount   Last remind│ │
│ │ Sham & Co   ...0040   28 May    9   ₹8,900   2d ago  [⟳] │ │
│ │ XYZ Ltd     ...0035   12 May   25  ₹45,000   never   [→] │ │
│ └─────────────────────────────────────────────────────────┘ │
│  [✓] select all     [ Send WhatsApp reminders (12) ]         │
└─────────────────────────────────────────────────────────────┘
```

## 13.9 AI Assistant

```
┌──────── Assistant ✦ ─────────────────────────────────────────┐
│                                                               │
│  You:   Who hasn't paid me?                                   │
│  ✦ AI:  You have 12 unpaid invoices totalling ₹2,30,000.      │
│         ┌───────────────────────────────────────────────┐    │
│         │ Top overdue: XYZ Ltd ₹45,000 (25 days) ...     │    │
│         └───────────────────────────────────────────────┘    │
│         [ Send reminders to all ]  [ Open collections ]       │
│                                                               │
│  You:   Invoice ABC Traders 50 bags cement at 350, 18%        │
│  ✦ AI:  Create invoice for ABC Traders — ₹20,650?             │
│         ┌─ Preview ─────────────────────────────────────┐     │
│         │ 50 BAG cement @ ₹350 · GST 18% · Total ₹20,650 │     │
│         └────────────────────────────────────────────────┘    │
│         [ ✓ Confirm ]   [ ✕ Cancel ]                          │
│                                                               │
│ ┌───────────────────────────────────────────────────  🎤 ┐  │
│ │ Type a message...                                    [➤] │  │
│ └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## 13.10 Settings

```
┌──────── Settings ────────────────────────────────────────────┐
│ Tabs: [Company] [Users & roles] [Invoice] [Notifications] [AI]│
│ Company name   [ ABC Traders Pvt Ltd            ]             │
│ GSTIN          [ 27ABCDE1234F1Z5 ]  State: Maharashtra (27)   │
│ Invoice prefix [ INV ]   Default due (days) [ 15 ]           │
│ WhatsApp number[ +91 ... ]  Template language [ EN ▾ / HI ]  │
│ Theme [ System ▾ ]                                            │
│                                          [ Save changes ]     │
└─────────────────────────────────────────────────────────────┘
```

## 13.11 States & accessibility

- Loading: skeleton rows/cards. Empty: friendly illustration + primary CTA.
- Errors: inline field errors + toast for request failures (from error envelope).
- All interactive elements keyboard-navigable; focus rings; ARIA labels (Radix/shadcn).
- Color contrast ≥ WCAG AA in both themes; status conveyed by icon + text, not color alone.
