# 8. Frontend Folder Structure

Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui. Feature-first
organisation, typed API client generated from the backend OpenAPI schema, React Query
for server state, Zustand for light UI state.

```
frontend/
├── package.json
├── next.config.mjs
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
├── components.json              # shadcn/ui config
├── Dockerfile
├── .env.example
├── public/
│   ├── logo.svg
│   └── icons/
└── src/
    ├── app/                     # App Router (routes = folders)
    │   ├── layout.tsx           # root layout: theme provider, fonts
    │   ├── globals.css          # Tailwind base + CSS vars (light/dark tokens)
    │   ├── page.tsx             # marketing/redirect → /dashboard or /login
    │   ├── login/
    │   │   └── page.tsx
    │   ├── (auth)/              # auth callback handling
    │   │   └── callback/page.tsx
    │   └── (app)/               # authenticated shell (sidebar + topbar)
    │       ├── layout.tsx       # guards session, renders AppShell
    │       ├── dashboard/page.tsx
    │       ├── invoices/
    │       │   ├── page.tsx          # list + search + filters
    │       │   ├── new/page.tsx      # create invoice
    │       │   └── [id]/page.tsx     # view/edit invoice
    │       ├── customers/
    │       │   ├── page.tsx
    │       │   └── [id]/page.tsx
    │       ├── collections/page.tsx
    │       ├── assistant/page.tsx    # AI copilot chat
    │       └── settings/page.tsx
    │
    ├── components/
    │   ├── ui/                  # shadcn/ui primitives (button, card, dialog, ...)
    │   ├── layout/
    │   │   ├── app-shell.tsx
    │   │   ├── sidebar.tsx
    │   │   ├── topbar.tsx
    │   │   └── theme-toggle.tsx
    │   ├── charts/              # revenue, aging, cashflow (recharts)
    │   ├── invoices/            # InvoiceForm, InvoiceTable, GstSummary
    │   ├── customers/
    │   ├── collections/
    │   ├── dashboard/           # MetricCard, AgingChart, CashflowChart
    │   └── assistant/           # ChatWindow, MessageBubble, ConfirmCard
    │
    ├── features/                # feature hooks/state colocated with API calls
    │   ├── invoices/
    │   │   ├── api.ts           # typed calls (uses lib/api-client)
    │   │   ├── hooks.ts         # useInvoices, useCreateInvoice (React Query)
    │   │   └── types.ts
    │   ├── customers/
    │   ├── collections/
    │   ├── dashboard/
    │   └── assistant/
    │
    ├── lib/
    │   ├── constants.ts         # ALL static values: routes, query keys, labels
    │   ├── api-client.ts        # fetch wrapper: auth header, error envelope, retry
    │   ├── generated/           # OpenAPI-generated types (openapi-typescript)
    │   ├── auth.ts              # session helpers (Entra/MSAL or NextAuth)
    │   ├── format.ts            # INR currency, dates (IST), GSTIN mask
    │   ├── query-client.ts      # React Query client
    │   └── utils.ts             # cn() etc.
    │
    ├── hooks/                   # generic hooks (useDebounce, useMediaQuery)
    ├── stores/                  # Zustand (ui store: sidebar, theme persisted)
    ├── styles/
    └── tests/
        ├── unit/                # vitest + testing-library
        └── e2e/                 # Playwright
```

## Conventions

- **Server state** via TanStack Query (`features/*/hooks.ts`); **UI state** via Zustand.
- **Typed API**: backend OpenAPI → `openapi-typescript` → `lib/generated`. `api-client.ts`
  attaches the JWT, unwraps the standard error envelope, and surfaces toasts.
- **Theming**: Tailwind CSS variables for light/dark; `next-themes` toggle; tokens defined once in `globals.css`.
- **Constants centralised** in `lib/constants.ts` (routes, React-Query keys, status labels,
  channel labels) — no magic strings in components (per project rule).
- **Accessibility**: shadcn/ui (Radix) primitives are keyboard- and screen-reader-friendly by default.
- **Responsive**: mobile-first; sidebar collapses to a sheet on small screens; PWA-installable.
