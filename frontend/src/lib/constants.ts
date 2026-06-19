export const APP_NAME = "KuberAIQ";
export const DEMO_LOGIN_EMAIL = "owner@demo.kuberaiq.com";
export const DEMO_CA_LOGIN_EMAIL = "ca@demo.kuberaiq.com";
export const E2E_EMAIL_DOMAIN = "@test.kuberaiq.com";
export const E2E_COMPANY_NAME_PREFIX = "E2E Traders";

/** Public production URLs (custom domain; overridden at Docker build via NEXT_PUBLIC_*). */
export const PUBLIC_WEB_URL =
  process.env.NEXT_PUBLIC_WEB_URL ?? "https://www.kuberaiq.com";
export const PUBLIC_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.kuberaiq.com";
export const PUBLIC_APEX_DOMAIN =
  process.env.NEXT_PUBLIC_APEX_DOMAIN ?? "kuberaiq.com";
/** Cloud Run default host suffix — same-origin API proxy via Next.js rewrites. */
export const CLOUD_RUN_HOST_SUFFIX = ".run.app";
export const LOCAL_API_URL = "http://localhost:8000";

export function isCloudRunHostname(hostname: string): boolean {
  return hostname.endsWith(CLOUD_RUN_HOST_SUFFIX);
}

export function usesSameOriginApi(hostname: string): boolean {
  return (
    hostname === PUBLIC_APEX_DOMAIN ||
    hostname.endsWith(`.${PUBLIC_APEX_DOMAIN}`) ||
    isCloudRunHostname(hostname)
  );
}

export const API_NETWORK_ERROR =
  "Cannot reach the API. Check your connection and open https://www.kuberaiq.com (not kuberaiq.com).";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "kuberaiq_access_token",
  REFRESH_TOKEN: "kuberaiq_refresh_token",
  USER: "kuberaiq_user",
} as const;

export const OAUTH_PROVIDER_MICROSOFT = "microsoft";
export const OAUTH_PROVIDER_GOOGLE = "google";
export const GOOGLE_OAUTH_SCOPES = "openid email profile";
/** PKCE verifier lifetime — must cover Google redirect round-trip. */
export const OAUTH_PKCE_TTL_SECONDS = 600;
/** Shared cookie domain for OAuth PKCE state (e.g. `.kuberaiq.com`). */
export const OAUTH_COOKIE_DOMAIN = process.env.NEXT_PUBLIC_OAUTH_COOKIE_DOMAIN ?? "";

export const USER_ROLE = {
  OWNER: "OWNER",
  STAFF: "STAFF",
  VIEWER: "VIEWER",
  CA: "CA",
} as const;

export type UserRole = (typeof USER_ROLE)[keyof typeof USER_ROLE];

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  AUTH_CALLBACK: "/auth/callback",
  ONBOARDING: "/onboarding",
  SUBSCRIBE: "/subscribe",
  DASHBOARD: "/dashboard",
  INVOICES: "/invoices",
  INVOICES_NEW: "/invoices/new",
  INVOICE_DETAIL: (id: string) => `/invoices/${id}` as const,
  PRODUCTS: "/products",
  QUOTATIONS: "/quotations",
  QUOTATIONS_NEW: "/quotations/new",
  QUOTATION_DETAIL: (id: string) => `/quotations/${id}` as const,
  CUSTOMERS: "/customers",
  CUSTOMER_DETAIL: (id: string) => `/customers/${id}` as const,
  COLLECTIONS: "/collections",
  ASSISTANT: "/assistant",
  COMPLIANCE: "/compliance",
  CA_CLIENTS: "/ca/clients",
  CA_DASHBOARD: "/ca/dashboard",
  SETTINGS: "/settings",
  EXPENSES: "/expenses",
  TERMS: "/terms",
  PRIVACY: "/privacy",
} as const;

export const API_PATHS = {
  MOCK_LOGIN: "/auth/mock-login",
  AUTH_CALLBACK: "/auth/callback",
  GOOGLE_CALLBACK: "/auth/google/callback",
  ME: "/auth/me",
  BILLING_STATUS: "/billing/status",
  BILLING_CHECKOUT: "/billing/checkout",
  BILLING_VERIFY: "/billing/verify",
  BILLING_MOCK_ACTIVATE: "/billing/mock-activate",
  REFRESH: "/auth/refresh",
  LOGOUT: "/auth/logout",
  COMPANY_ONBOARD: "/companies/onboard",
  COMPANY_ME: "/companies/me",
  AUDIT_LOGS: "/audit-logs",
  CUSTOMERS: "/customers",
  CUSTOMERS_CHECK_PHONE: "/customers/check-phone",
  PRODUCTS: "/products",
  PRODUCTS_HSN_LOOKUP: "/products/hsn-lookup",
  QUOTATIONS: "/quotations",
  QUOTATION_SEND: (id: string) => `/quotations/${id}:send` as const,
  QUOTATION_CONVERT: (id: string) => `/quotations/${id}:convert` as const,
  QUOTATION_PDF: (id: string) => `/quotations/${id}/pdf` as const,
  QUOTATION_PDF_DOWNLOAD: (id: string) => `/quotations/${id}/pdf/download` as const,
  INVOICES: "/invoices",
  INVOICE_PAYMENT_LINK: (id: string) => `/invoices/${id}/payment-link` as const,
  INVOICE_CREDIT_NOTES: (id: string) => `/invoices/${id}/credit-notes` as const,
  GST_REPORT: "/invoices/reports/gst",
  GST_REPORT_CSV: "/invoices/reports/gst.csv",
  GSTR1_REPORT: "/invoices/reports/gstr1",
  GSTR1_REPORT_CSV: "/invoices/reports/gstr1.csv",
  GSTR3B_REPORT: "/invoices/reports/gstr3b",
  GSTR3B_REPORT_CSV: "/invoices/reports/gstr3b.csv",
  COLLECTIONS_OVERDUE: "/collections/overdue",
  COLLECTIONS_DASHBOARD: "/collections/dashboard",
  COLLECTIONS_REMINDERS: "/collections/reminders",
  COLLECTIONS_REMINDER_PREVIEW: "/collections/reminders/preview",
  COLLECTIONS_BULK_PREVIEW: "/collections/reminders/bulk:preview",
  COLLECTIONS_BULK_SEND: "/collections/reminders/bulk",
  COLLECTIONS_CALL_TODAY: "/collections/call-today",
  CUSTOMER_STATEMENT: (id: string) => `/customers/${id}/statement.pdf` as const,
  CUSTOMER_LEDGER: (id: string) => `/customers/${id}/ledger` as const,
  DASHBOARD: "/dashboard",
  COMPLIANCE_DASHBOARD: "/compliance/dashboard",
  COMPLIANCE_OBLIGATIONS: "/compliance/obligations",
  COMPLIANCE_CALENDAR: "/compliance/calendar",
  COMPLIANCE_COMPLETE: (id: string) => `/compliance/obligations/${id}/complete` as const,
  COMPLIANCE_PROFILE: "/compliance/profile",
  COMPLIANCE_ALERTS_PREVIEW: "/compliance/alerts/preview",
  CA_CLIENTS: "/ca/clients",
  CA_DASHBOARD: "/ca/dashboard",
  CA_ACCEPT_INVITE: (id: string) => `/ca/invitations/${id}/accept` as const,
  CA_CONTEXT: "/ca/context",
  CA_CONTEXT_CLEAR: "/ca/context/clear",
  ADVISORS: "/companies/me/advisors",
  COMPANY_STAFF: "/companies/me/staff",
  COMPANY_STAFF_REVOKE: (id: string) => `/companies/me/staff/${id}` as const,
  ADVISOR_REVOKE: (id: string) => `/companies/me/advisors/${id}` as const,
  ME_WHATSAPP_PHONE: "/auth/me/whatsapp-phone",
  AI_CHAT: "/ai/chat",
  AI_CONFIRM: "/ai/confirm",
  EXPENSES: "/expenses",
  CA_GSTR1_BULK: "/ca/reports/gstr1/bulk",
} as const;

export const QUERY_KEYS = {
  ME: ["auth", "me"] as const,
  DASHBOARD: (from?: string, to?: string) => ["dashboard", from, to] as const,
  INVOICES: (params?: object) => ["invoices", params] as const,
  INVOICE: (id: string) => ["invoices", id] as const,
  PRODUCTS: (params?: object) => ["products", params] as const,
  PRODUCT: (id: string) => ["products", id] as const,
  QUOTATIONS: (params?: object) => ["quotations", params] as const,
  QUOTATION: (id: string) => ["quotations", id] as const,
  CUSTOMERS: (params?: object) => ["customers", params] as const,
  CUSTOMER: (id: string) => ["customers", id] as const,
  CREDIT_NOTES: (invoiceId: string) => ["invoices", invoiceId, "credit-notes"] as const,
  COLLECTIONS_OVERDUE: (params?: object) => ["collections", "overdue", params] as const,
  COLLECTIONS_DASHBOARD: ["collections", "dashboard"] as const,
  COLLECTIONS_CALL_TODAY: ["collections", "call-today"] as const,
  AI_SESSION: (id: string) => ["ai", "session", id] as const,
  COMPANY: ["company", "me"] as const,
  AUDIT_LOGS: ["audit", "logs"] as const,
  GST_REPORT: (from: string, to: string) => ["gst-report", from, to] as const,
  GSTR1_REPORT: (from: string, to: string) => ["gstr1-report", from, to] as const,
  GSTR3B_REPORT: (from: string, to: string) => ["gstr3b-report", from, to] as const,
  COMPLIANCE_ALERTS: ["compliance", "alerts"] as const,
  BILLING_STATUS: ["billing", "status"] as const,
  COMPLIANCE: ["compliance", "dashboard"] as const,
  COMPLIANCE_OBLIGATIONS: ["compliance", "obligations"] as const,
  COMPLIANCE_CALENDAR: (days?: number) => ["compliance", "calendar", days] as const,
  CA_CLIENTS: ["ca", "clients"] as const,
  CA_DASHBOARD: ["ca", "dashboard"] as const,
  ADVISORS: ["advisors"] as const,
} as const;

export const NAV_ITEMS_CA = [
  { href: ROUTES.CA_DASHBOARD, label: "Dashboard", icon: "LayoutDashboard" },
  { href: ROUTES.CA_CLIENTS, label: "Clients", icon: "Users" },
  { href: ROUTES.COMPLIANCE, label: "Compliance", icon: "ShieldCheck" },
  { href: ROUTES.SETTINGS, label: "Reports", icon: "Settings" },
] as const;

export const NAV_ITEMS = [
  { href: ROUTES.DASHBOARD, label: "Dashboard", icon: "LayoutDashboard" },
  { href: ROUTES.INVOICES, label: "Invoices", icon: "FileText" },
  { href: ROUTES.QUOTATIONS, label: "Quotations", icon: "ClipboardList" },
  { href: ROUTES.PRODUCTS, label: "Products", icon: "Package" },
  { href: ROUTES.CUSTOMERS, label: "Customers", icon: "Users" },
  { href: ROUTES.COLLECTIONS, label: "Collections", icon: "IndianRupee" },
  { href: ROUTES.COMPLIANCE, label: "Compliance", icon: "ShieldCheck" },
  { href: ROUTES.ASSISTANT, label: "Assistant", icon: "Bot" },
  { href: ROUTES.EXPENSES, label: "Expenses", icon: "IndianRupee" },
  { href: ROUTES.SETTINGS, label: "Settings", icon: "Settings" },
] as const;

export const INVOICE_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  ISSUED: "Issued",
  PARTIALLY_PAID: "Partially Paid",
  PAID: "Paid",
  OVERDUE: "Overdue",
  CANCELLED: "Cancelled",
};

export const INVOICE_STATUS_FILTER_OPTIONS = [
  { value: "", label: "All statuses" },
  ...Object.entries(INVOICE_STATUS_LABELS).map(([value, label]) => ({ value, label })),
] as const;

export const INVOICE_STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  DRAFT: "secondary",
  ISSUED: "default",
  PARTIALLY_PAID: "outline",
  PAID: "default",
  OVERDUE: "destructive",
  CANCELLED: "secondary",
};

export const AGING_BUCKET_LABELS: Record<string, string> = {
  "0-30": "0–30 days",
  "31-60": "31–60 days",
  "61-90": "61–90 days",
  "90+": "90+ days",
};

export const PAGE_TITLES: Record<string, string> = {
  [ROUTES.DASHBOARD]: "Dashboard",
  [ROUTES.INVOICES]: "Invoices",
  [ROUTES.PRODUCTS]: "Products",
  [ROUTES.QUOTATIONS]: "Quotations",
  [ROUTES.CUSTOMERS]: "Customers",
  [ROUTES.COLLECTIONS]: "Collections",
  [ROUTES.COMPLIANCE]: "Compliance",
  [ROUTES.CA_CLIENTS]: "Clients",
  [ROUTES.CA_DASHBOARD]: "CA Dashboard",
  [ROUTES.ASSISTANT]: "AI Assistant",
  [ROUTES.EXPENSES]: "Expenses",
  [ROUTES.SETTINGS]: "Settings",
};

export const DEFAULT_PAGE_SIZE = 20;
export const DEFAULT_DUE_DAYS = 15;
export const HSN_LOOKUP_MIN_CHARS = 3;
export const HSN_LOOKUP_DEBOUNCE_MS = 400;

export const GST_RATES = [0, 5, 12, 18, 28] as const;

export const PAYMENT_METHODS = [
  { value: "CASH", label: "Cash" },
  { value: "UPI", label: "UPI" },
  { value: "BANK_TRANSFER", label: "Bank Transfer" },
  { value: "CHEQUE", label: "Cheque" },
  { value: "CARD", label: "Card" },
  { value: "OTHER", label: "Other" },
] as const;

export const PAYMENT_METHOD_LABELS: Record<string, string> = Object.fromEntries(
  PAYMENT_METHODS.map((method) => [method.value, method.label]),
);

export const INVOICE_UNITS = ["NOS", "BAG", "KG", "MT", "LTR", "BOX"] as const;

export const CUSTOMER_FORM = {
  TITLE: "Add customer",
  EDIT_TITLE: "Edit customer",
  DESCRIPTION: "Enter complete billing details for GST-compliant invoices.",
  SECTION_BUSINESS: "Business details",
  SECTION_CONTACT: "Contact",
  SECTION_BILLING: "Billing address",
  COMPANY_NAME: "Company / business name",
  GSTIN: "GSTIN",
  GSTIN_HINT: "15-character GSTIN; state code is derived automatically.",
  PHONE: "Mobile number",
  EMAIL: "Email address",
  ADDRESS: "Billing address",
  NOTES: "Notes (optional)",
} as const;

export const GST_REPORT = {
  TITLE: "GST summary report",
  DESCRIPTION: "Export issued invoice totals for your CA or GSTR filing.",
  FROM_LABEL: "From date",
  TO_LABEL: "To date",
  INVALID_RANGE: "From date must be on or before to date.",
  REFRESH_LABEL: "Load summary",
  DOWNLOAD_LABEL: "Download CSV",
  LOAD_ERROR: "Failed to load GST report",
  INVOICE_COUNT: "Invoices",
  TAXABLE: "Taxable value",
  CGST: "CGST",
  SGST: "SGST",
  IGST: "IGST",
  TOTAL_TAX: "Total tax",
  GRAND_TOTAL: "Grand total",
} as const;

export const GSTR_EXPORT = {
  GSTR1_TITLE: "GSTR-1 export",
  GSTR1_DESCRIPTION: "Outward supply summary (B2B, B2C, HSN) for GSTR-1 filing.",
  GSTR3B_TITLE: "GSTR-3B export",
  GSTR3B_DESCRIPTION: "Outward tax summary for GSTR-3B return.",
  VIEW_JSON: "View JSON",
  HIDE_JSON: "Hide JSON",
  DOWNLOAD_CSV: "Download CSV",
  LOAD_ERROR: "Failed to load report",
  OUTWARD_TAXABLE: "Outward taxable",
  OUTWARD_CGST: "Outward CGST",
  OUTWARD_SGST: "Outward SGST",
  OUTWARD_IGST: "Outward IGST",
  TOTAL_OUTWARD_TAX: "Total outward tax",
  B2B_COUNT: "B2B invoices",
  CREDIT_NOTES: "Credit notes",
} as const;

export const QUOTATION_STATUS_LABELS: Record<string, string> = {
  DRAFT: "Draft",
  SENT: "Sent",
  ACCEPTED: "Accepted",
  REJECTED: "Rejected",
  EXPIRED: "Expired",
  CONVERTED: "Converted",
};

export const QUOTATION_STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  DRAFT: "secondary",
  SENT: "default",
  ACCEPTED: "outline",
  REJECTED: "destructive",
  EXPIRED: "destructive",
  CONVERTED: "default",
};

export const QUOTATION_STATUS_FILTER_OPTIONS = [
  { value: "", label: "All statuses" },
  ...Object.entries(QUOTATION_STATUS_LABELS).map(([value, label]) => ({ value, label })),
] as const;

export const PRODUCT_FORM = {
  TITLE: "Add product",
  EDIT_TITLE: "Edit product",
  DESCRIPTION: "Catalog items pre-fill invoice and quotation line items.",
  NAME: "Product name",
  DESCRIPTION_FIELD: "Description (optional)",
  HSN_SAC: "HSN / SAC",
  UNIT: "Unit",
  DEFAULT_PRICE: "Default price (₹)",
  GST_RATE: "GST rate",
  GST_AUTO_FILLED: "Auto-filled from HSN/SAC — you can override",
  GST_MATCHED: "Matched GST catalogue:",
  DEACTIVATE: "Deactivate",
  DEACTIVATE_CONFIRM: "Deactivate this product? It will no longer appear in the catalog picker.",
} as const;

export const QUOTATION_COPY = {
  TITLE: "Quotations",
  DESCRIPTION: "Send estimates and convert accepted quotes to invoices",
  NEW_TITLE: "New quotation",
  SEND: "Send quotation",
  CONVERT: "Convert to invoice",
  VALID_UNTIL: "Valid until",
  CONVERTED_LINK: "View invoice",
} as const;

export const CREDIT_NOTE_COPY = {
  BUTTON: "Issue credit note",
  TITLE: "Issue credit note",
  DESCRIPTION: "Creates a credit note for the full invoice amount and reduces outstanding balance.",
  REASON: "Reason",
  REASON_PLACEHOLDER: "Returned goods, pricing correction, etc.",
  SUBMIT: "Issue credit note",
  LIST_TITLE: "Credit notes",
} as const;

export const INVOICE_LINE_MODE = {
  CATALOG: "From catalog",
  CUSTOM: "Custom line",
} as const;

export const ASSISTANT_CHANNEL = "web";

export const ASSISTANT_CONFIRM_WORDS = new Set([
  "yes",
  "confirm",
  "ok",
  "proceed",
  "go ahead",
]);

export const ASSISTANT_CANCEL_WORDS = new Set(["no", "cancel", "stop", "abort"]);

export const CASHFLOW_DISCLAIMER =
  "Expected inflows based on invoice due dates and balances — not guaranteed.";

export const CASHFLOW_FORECAST_DISCLAIMER =
  "30-day forecast uses open receivables by due date. For planning only — not financial advice.";

export const COMPLIANCE_STATUS_LABELS: Record<string, string> = {
  UPCOMING: "Upcoming",
  DUE_SOON: "Due soon",
  OVERDUE: "Overdue",
  PENDING: "Pending",
  COMPLETED: "Completed",
  NOT_APPLICABLE: "N/A",
};

export const COMPLIANCE_STATUS_VARIANTS: Record<
  string,
  "default" | "secondary" | "destructive" | "outline"
> = {
  UPCOMING: "secondary",
  DUE_SOON: "outline",
  OVERDUE: "destructive",
  PENDING: "secondary",
  COMPLETED: "default",
  NOT_APPLICABLE: "outline",
};

export const COMPLIANCE_CATEGORY_LABELS: Record<string, string> = {
  GST: "GST",
  INCOME_TAX: "Income Tax",
  LABOUR: "Labour & Statutory",
  MCA: "MCA / Corporate",
  OTHER: "Other",
};

export const COMPLIANCE_ENTITY_TYPES = [
  { value: "PROPRIETORSHIP", label: "Proprietorship" },
  { value: "PARTNERSHIP", label: "Partnership" },
  { value: "LLP", label: "LLP" },
  { value: "PRIVATE_LIMITED", label: "Private Limited" },
  { value: "PUBLIC_LIMITED", label: "Public Limited" },
] as const;

export const COMPLIANCE_TURNOVER_BANDS = [
  { value: "BELOW_40L", label: "Below ₹40 lakh" },
  { value: "_40L_100L", label: "₹40 lakh – ₹1 crore" },
  { value: "_100L_500L", label: "₹1 crore – ₹5 crore" },
  { value: "ABOVE_500L", label: "Above ₹5 crore" },
] as const;

export const COMPLIANCE_GSTR1_FREQUENCIES = [
  { value: "MONTHLY", label: "Monthly" },
  { value: "QUARTERLY", label: "Quarterly (QRMP)" },
] as const;

export const COMPLIANCE_COPY = {
  TITLE: "Compliance center",
  DESCRIPTION: "Track GST, tax, labour, and statutory obligations tailored to your MSME profile.",
  OVERVIEW_TITLE: "Compliance health",
  DEADLINES_TITLE: "Upcoming deadlines",
  OBLIGATIONS_TITLE: "Applicable obligations",
  CALENDAR_TITLE: "Compliance calendar",
  PROFILE_TITLE: "Business profile for compliance",
  PROFILE_INCOMPLETE: "Complete your business profile to see applicable compliances.",
  PROFILE_HINT: "Set turnover band, entity type, and filing frequency to personalize obligations.",
  EINVOICE_TITLE: "E-invoice readiness",
  EINVOICE_THRESHOLD: "Mandatory when FY turnover crosses ₹10 lakh (Apr 2025 rule).",
  YTD_TURNOVER: "FY turnover (issued invoices)",
  PENDING_IRN: "Invoices without IRN",
  CHECKLIST_TITLE: "Filing checklist",
  MARK_COMPLETE: "Mark complete",
  LEARN_MORE: "Open related action",
  SAVE_PROFILE: "Save compliance profile",
  IRN_LABEL: "Invoice Reference Number (IRN)",
  IRN_HINT: "Generate on the GST IRP portal, then record the 64-character IRN here.",
  IRN_SAVE: "Save IRN",
  IRN_REQUIRED: "E-invoicing required — register IRN within 30 days of issue.",
  HEALTH_SCORE: "Health score",
  OVERDUE: "Overdue",
  DUE_THIS_WEEK: "Due this week",
  NOT_APPLICABLE_TITLE: "Not applicable",
  COMPLIANCE_ALERTS_PREVIEW: "Upcoming compliance alerts",
  ALERTS_EMPTY: "No obligations due in the next few days.",
} as const;

export const CA_COPY = {
  CLIENTS_TITLE: "Your clients",
  CLIENTS_DESCRIPTION: "MSME businesses you advise — accept invites and open a client workspace.",
  DASHBOARD_TITLE: "Filing overview",
  DASHBOARD_DESCRIPTION: "Upcoming GST and compliance deadlines across your active clients.",
  PENDING_INVITES: "Pending invitations",
  ACTIVE_CLIENTS: "Active clients",
  ACCEPT_INVITE: "Accept invite",
  OPEN_CLIENT: "Open client",
  CLEAR_CLIENT: "Clear client context",
  NO_CLIENTS: "No client assignments yet. Ask an MSME owner to invite you from Settings.",
  FIRM_LABEL: "Firm",
  STATUS_PENDING: "Pending",
  STATUS_ACTIVE: "Active",
  STATUS_REVOKED: "Revoked",
  SWITCHER_LABEL: "Acting for",
  SWITCHER_PLACEHOLDER: "Select client",
  ADVISORS_TITLE: "Chartered accountants",
  ADVISORS_DESCRIPTION: "Invite your CA to view compliance and GSTR reports for this business.",
  INVITE_CA: "Invite CA",
  REVOKE_CA: "Revoke access",
  CA_EMAIL: "CA email",
  CA_FIRM: "CA firm name (optional)",
  INVITE_SENT: "Invitation sent.",
  INVITE_ERROR: "Could not send invitation.",
} as const;

export const E_INVOICE_TURNOVER_THRESHOLD = 1_000_000;

export const REMINDER_LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
] as const;

export const COLLECTIONS_COPY = {
  CALL_TODAY_TITLE: "Call today",
  CALL_TODAY_DESCRIPTION: "Priority follow-ups due soon or overdue — sorted by amount and urgency.",
  CALL_TODAY_EMPTY: "No invoices need follow-up today.",
  DUE_SOON: "Due soon",
  DUE_TODAY: "Due today",
  OVERDUE: "Overdue",
  AUTO_REMINDERS_ON:
    "Automated WhatsApp reminders are on. They run daily at 9 AM IST for due-soon, due-today, and overdue milestones.",
  AUTO_REMINDERS_OFF:
    "Automated reminders are off. Enable them in Settings → Payments & reminders to follow up automatically.",
} as const;

export const RAZORPAY_CHECKOUT_SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js";

export const BILLING_SETTINGS = {
  TITLE: "KuberAIQ subscription",
  DESCRIPTION: "Your platform plan — separate from customer UPI/payment settings below.",
  PLAN_LABEL: "Plan",
  STATUS_LABEL: "Status",
  VALID_UNTIL_LABEL: "Valid until",
  AMOUNT_LABEL: "Amount",
  RENEW_CTA: "Renew subscription",
  PAY_CTA: "Complete payment",
  ACTIVE_NOTE: "Your subscription is active. You can use the full workspace until the date above.",
  EXPIRED_NOTE: "Your subscription has ended. Renew to continue using KuberAIQ.",
  PENDING_NOTE: "Payment is required before you can finish business setup.",
  STATUS_LABELS: {
    PENDING: "Payment pending",
    ACTIVE: "Active",
    EXPIRED: "Expired",
    CANCELLED: "Cancelled",
  } as Record<string, string>,
} as const;

export const SUBSCRIPTION_PAGE = {
  TITLE: "Activate your subscription",
  DESCRIPTION: "Complete payment to unlock your workspace and set up your business.",
  PLAN_NAME: "KuberAIQ Starter",
  BILLING_CYCLE: "per month · 30-day access",
  PAY_CTA: "Pay securely with Razorpay",
  MOCK_PAY_CTA: "Activate (demo — no charge)",
  PAYING: "Processing payment…",
  PAYMENT_CANCELLED: "Payment cancelled. You can try again when ready.",
  PAYMENT_SUCCESS: "Payment successful — setting up your workspace…",
  SECURE_NOTE: "Secured by Razorpay · UPI, cards, netbanking & wallets",
  ACCOUNT_LABEL: "Account",
  STEPS: ["Sign in", "Pay", "Set up business"] as const,
  STEP_ACTIVE: 1,
  FEATURES: [
    "GST invoicing, quotations & credit notes",
    "Collections, reminders & customer ledger",
    "MSME compliance calendar & GSTR exports",
    "AI business assistant",
    "Dedicated workspace — your data stays separate",
  ],
} as const;

export const PAYMENTS_SETTINGS = {
  TITLE: "Payments & reminders",
  DESCRIPTION: "UPI details appear on invoice PDFs. Automated reminders run daily at 9 AM IST.",
  UPI_ID: "UPI ID (VPA)",
  UPI_PAYEE_NAME: "UPI payee name",
  AUTO_REMINDERS: "Send automated payment reminders",
  DEFAULT_LANGUAGE: "Default reminder language",
  SAVE_LABEL: "Save payment settings",
} as const;

export const WHATSAPP_COPILOT_SETTINGS = {
  TITLE: "WhatsApp AI copilot",
  DESCRIPTION:
    "Link your WhatsApp number to chat with the same AI assistant you use on the web — ask about invoices, collections, and compliance.",
  PHONE_LABEL: "Your WhatsApp mobile number",
  PHONE_HINT: "10-digit Indian mobile (the number you message from).",
  SAVE_LABEL: "Save WhatsApp number",
  SAVED: "WhatsApp number linked for AI copilot.",
  CLEARED: "WhatsApp copilot link removed.",
  SAVE_ERROR: "Could not save WhatsApp number.",
} as const;

export const CUSTOMER_STATEMENT = {
  DOWNLOAD_LABEL: "Download statement",
  DOWNLOADING: "Preparing PDF…",
} as const;

export const LANDING_COPY = {
  TAGLINE: "AI-powered billing, collections & compliance for Indian MSMEs",
  HERO_TITLE: "Run your business smarter — invoices to compliance in one place",
  HERO_SUBTITLE:
    "Create GST invoices, chase payments, track statutory deadlines, and get AI guidance — built for shop owners and small traders.",
  CTA_PRIMARY: "Start free",
  CTA_SECONDARY: "Sign in",
  FEATURES_TITLE: "Everything you need to get paid and stay compliant",
  FEATURE_INVOICES: "GST invoices & PDFs",
  FEATURE_INVOICES_DESC: "Professional invoices with UPI QR codes for faster collections.",
  FEATURE_COLLECTIONS: "Smart collections",
  FEATURE_COLLECTIONS_DESC: "Overdue tracking, call-today priorities, and automated reminders.",
  FEATURE_COMPLIANCE: "MSME compliance calendar",
  FEATURE_COMPLIANCE_DESC: "Know what applies to you — GSTR, ITR, labour filings, and due dates.",
  FEATURE_AI: "AI business assistant",
  FEATURE_AI_DESC: "Ask questions about pending payments, cash flow, and daily operations.",
  TRUST_LINE: "Free to start · No credit card · Data stored securely in India (Azure)",
} as const;

export const MSME_LOGIN_SEGMENTS = [
  {
    id: "kirana",
    label: { en: "Kirana & retail", hi: "किराना और रिटेल" },
    headline: { en: "Bill faster. Track udhaar.", hi: "तेज़ बिलिंग। उधार ट्रैक करें।" },
    highlights: {
      en: ["GST bills in seconds", "Customer ledger & dues", "WhatsApp payment reminders"],
      hi: ["सेकंडों में GST बिल", "ग्राहक खाता और बकाया", "व्हाट्सऐप पेमेंट रिमाइंडर"],
    },
  },
  {
    id: "trader",
    label: { en: "Traders & wholesale", hi: "ट्रेडर और थोक" },
    headline: { en: "Multi-item invoices. One tap GST.", hi: "मल्टी-आइटम इनवॉइस। एक टैप GST।" },
    highlights: {
      en: ["HSN auto-fill from product name", "Quotations → invoices", "Overdue collections"],
      hi: ["प्रोडक्ट नाम से HSN", "कोटेशन से इनवॉइस", "बकाया वसूली"],
    },
  },
  {
    id: "manufacturing",
    label: { en: "Manufacturing", hi: "विनिर्माण" },
    headline: { en: "Raw material to invoice.", hi: "कच्चा माल से इनवॉइस तक।" },
    highlights: {
      en: ["Batch & unit pricing", "GSTR-ready exports", "Inventory-aware billing"],
      hi: ["बैच और यूनिट प्राइसिंग", "GSTR रिपोर्ट", "इन्वेंटरी बिलिंग"],
    },
  },
  {
    id: "services",
    label: { en: "Services & professionals", hi: "सेवाएं और प्रोफेशनल" },
    headline: { en: "Quote. Deliver. Get paid.", hi: "कोट करें। डिलीवर करें। पेमेंट लें।" },
    highlights: {
      en: ["SAC codes for services", "Recurring invoices", "AI assistant for follow-ups"],
      hi: ["सेवाओं के लिए SAC", "रिकरिंग इनवॉइस", "AI असिस्टेंट"],
    },
  },
  {
    id: "construction",
    label: { en: "Hardware & contractors", hi: "हार्डवेयर और ठेकेदार" },
    headline: { en: "Cement to sealant — billed right.", hi: "सीमेंट से सीलेंट — सही बिलिंग।" },
    highlights: {
      en: ["Multi-line material invoices", "Site-wise customer accounts", "GST on construction goods"],
      hi: ["मल्टी-लाइन मटीरियल बिल", "साइट-वाइज ग्राहक", "निर्माण सामान पर GST"],
    },
  },
  {
    id: "food",
    label: { en: "Food & hospitality", hi: "फूड और हॉस्पिटैलिटी" },
    headline: { en: "Daily sales. Weekly GST clarity.", hi: "रोज़ की बिक्री। साप्ताहिक GST स्पष्टता।" },
    highlights: {
      en: ["Fast billing at counter", "Supplier payment tracking", "Compliance calendar"],
      hi: ["काउंटर पर तेज़ बिल", "सप्लायर पेमेंट ट्रैक", "कंप्लायंस कैलेंडर"],
    },
  },
] as const;

export type MsmeLoginSegmentId = (typeof MSME_LOGIN_SEGMENTS)[number]["id"];

export const LOGIN_STORAGE_KEYS = {
  MSME_SEGMENT: "kuberaiq_msme_segment",
  REMEMBER_EMAIL: "kuberaiq_remember_email",
  QUICK_START_DISMISSED: "kuberaiq_msme_quickstart_dismissed",
  STARTER_PRODUCTS_IMPORTED: "kuberaiq_starter_products_imported",
} as const;

export interface MsmeStarterProduct {
  name: string;
  hsn_sac: string;
  unit: string;
  default_price: number;
  gst_rate: number;
}

export const MSME_STARTER_PRODUCTS: Record<MsmeLoginSegmentId, MsmeStarterProduct[]> = {
  kirana: [
    { name: "Basmati Rice 5kg", hsn_sac: "100630", unit: "BAG", default_price: 650, gst_rate: 0 },
    { name: "Toor Dal 1kg", hsn_sac: "071320", unit: "KG", default_price: 140, gst_rate: 0 },
    { name: "Sunflower Oil 1L", hsn_sac: "151219", unit: "LTR", default_price: 165, gst_rate: 5 },
    { name: "Biscuits Pack", hsn_sac: "190531", unit: "NOS", default_price: 30, gst_rate: 12 },
  ],
  trader: [
    { name: "Cement 50kg Bag", hsn_sac: "252329", unit: "BAG", default_price: 380, gst_rate: 28 },
    { name: "TMT Steel 12mm", hsn_sac: "721420", unit: "TON", default_price: 62000, gst_rate: 18 },
    { name: "Wall Putty 40kg", hsn_sac: "321410", unit: "BAG", default_price: 850, gst_rate: 18 },
    { name: "PVC Pipe 4 inch", hsn_sac: "391723", unit: "NOS", default_price: 420, gst_rate: 18 },
  ],
  manufacturing: [
    { name: "Raw Cotton Bale", hsn_sac: "520100", unit: "BALE", default_price: 45000, gst_rate: 5 },
    { name: "Finished Fabric Roll", hsn_sac: "520852", unit: "MTR", default_price: 85, gst_rate: 12 },
    { name: "Industrial Lubricant", hsn_sac: "271019", unit: "LTR", default_price: 220, gst_rate: 18 },
    { name: "Packaging Carton", hsn_sac: "481910", unit: "NOS", default_price: 35, gst_rate: 12 },
  ],
  services: [
    { name: "Consulting — per hour", hsn_sac: "998312", unit: "HRS", default_price: 2500, gst_rate: 18 },
    { name: "Annual Maintenance Contract", hsn_sac: "998313", unit: "NOS", default_price: 15000, gst_rate: 18 },
    { name: "Software Setup Fee", hsn_sac: "998314", unit: "NOS", default_price: 5000, gst_rate: 18 },
    { name: "Training Session", hsn_sac: "999293", unit: "NOS", default_price: 8000, gst_rate: 18 },
  ],
  construction: [
    { name: "OPC Cement 50kg", hsn_sac: "252329", unit: "BAG", default_price: 380, gst_rate: 28 },
    { name: "Construction Sealant", hsn_sac: "321410", unit: "NOS", default_price: 450, gst_rate: 18 },
    { name: "River Sand", hsn_sac: "250590", unit: "TON", default_price: 3500, gst_rate: 5 },
    { name: "Brick Red", hsn_sac: "690100", unit: "NOS", default_price: 8, gst_rate: 12 },
  ],
  food: [
    { name: "Thali Meal", hsn_sac: "996331", unit: "NOS", default_price: 120, gst_rate: 5 },
    { name: "Beverage 300ml", hsn_sac: "220210", unit: "NOS", default_price: 40, gst_rate: 12 },
    { name: "Snacks Plate", hsn_sac: "210690", unit: "NOS", default_price: 80, gst_rate: 5 },
    { name: "Catering Per Person", hsn_sac: "996334", unit: "NOS", default_price: 350, gst_rate: 5 },
  ],
};

export const MSME_QUICK_START_ACTIONS: Record<
  MsmeLoginSegmentId,
  Array<{ label: { en: string; hi: string }; href: string; assistantPrompt?: string }>
> = {
  kirana: [
    { label: { en: "Create GST bill", hi: "GST बिल बनाएं" }, href: ROUTES.INVOICES_NEW },
    { label: { en: "Add customer", hi: "ग्राहक जोड़ें" }, href: ROUTES.CUSTOMERS },
    {
      label: { en: "Who owes me?", hi: "किसका बकाया है?" },
      href: ROUTES.ASSISTANT,
      assistantPrompt: "Show customers with overdue payments",
    },
  ],
  trader: [
    { label: { en: "Multi-item invoice", hi: "मल्टी-आइटम इनवॉइस" }, href: ROUTES.INVOICES_NEW },
    { label: { en: "Import products", hi: "प्रोडक्ट इम्पोर्ट" }, href: ROUTES.PRODUCTS },
    {
      label: { en: "GST summary", hi: "GST सारांश" },
      href: ROUTES.ASSISTANT,
      assistantPrompt: "Summarize GST liability this month",
    },
  ],
  manufacturing: [
    { label: { en: "Add raw material", hi: "कच्चा माल जोड़ें" }, href: ROUTES.PRODUCTS },
    { label: { en: "Create invoice", hi: "इनवॉइस बनाएं" }, href: ROUTES.INVOICES_NEW },
    { label: { en: "GSTR report", hi: "GSTR रिपोर्ट" }, href: ROUTES.SETTINGS },
  ],
  services: [
    { label: { en: "New quotation", hi: "नया कोटेशन" }, href: ROUTES.QUOTATIONS_NEW },
    { label: { en: "Record payment", hi: "पेमेंट रिकॉर्ड" }, href: ROUTES.COLLECTIONS },
    {
      label: { en: "Follow up dues", hi: "बकाया फॉलो-अप" },
      href: ROUTES.ASSISTANT,
      assistantPrompt: "List overdue invoices and suggest follow-up messages",
    },
  ],
  construction: [
    { label: { en: "Material invoice", hi: "मटीरियल इनवॉइस" }, href: ROUTES.INVOICES_NEW },
    { label: { en: "Site customer", hi: "साइट ग्राहक" }, href: ROUTES.CUSTOMERS },
    {
      label: { en: "Invoice cement + sealant", hi: "सीमेंट + सीलेंट बिल" },
      href: ROUTES.ASSISTANT,
      assistantPrompt: "Create invoice for 50 bags cement and 10 sealant tubes for AIMLGYAN",
    },
  ],
  food: [
    { label: { en: "Daily sales bill", hi: "दैनिक बिक्री बिल" }, href: ROUTES.INVOICES_NEW },
    { label: { en: "Supplier expense", hi: "सप्लायर खर्च" }, href: ROUTES.EXPENSES },
    { label: { en: "Compliance dates", hi: "कंप्लायंस तारीखें" }, href: ROUTES.COMPLIANCE },
  ],
};

export const MSME_ASSISTANT_PROMPTS: Record<MsmeLoginSegmentId, string[]> = {
  kirana: [
    "Show customers with pending udhaar",
    "Create invoice for 2kg dal and 1L oil for Ramesh",
    "Who paid me this week?",
  ],
  trader: [
    "Create invoice for 50 cement bags for ABC Traders",
    "Show overdue invoices above ₹10,000",
    "Summarize collections this month",
  ],
  manufacturing: [
    "List top selling products this quarter",
    "Create invoice for 100m fabric roll",
    "Show GST output tax summary",
  ],
  services: [
    "Create quotation for AMC ₹15,000",
    "List overdue invoices for follow-up",
    "Summarize revenue this month",
  ],
  construction: [
    "Invoice 50 bags cement and 10 sealant for site customer",
    "Show overdue payments from contractors",
    "Add customer with phone 9876543210",
  ],
  food: [
    "Show today's sales summary",
    "Create invoice for catering 50 persons",
    "List supplier payments due",
  ],
};

export const MSME_QUICK_START_COPY = {
  TITLE: { en: "Quick start for your business", hi: "आपके व्यवसाय के लिए त्वरित शुरुआत" },
  DISMISS: { en: "Dismiss", hi: "बंद करें" },
  IMPORT_TITLE: { en: "Import starter products", hi: "स्टार्टर प्रोडक्ट इम्पोर्ट करें" },
  IMPORT_DESC: {
    en: "Add common items for your business type — edit prices anytime.",
    hi: "अपने व्यवसाय के सामान्य आइटम जोड़ें — कीमतें बाद में बदल सकते हैं।",
  },
  IMPORT_BUTTON: { en: "Import {count} products", hi: "{count} प्रोडक्ट इम्पोर्ट करें" },
  IMPORTING: { en: "Importing…", hi: "इम्पोर्ट हो रहा है…" },
  IMPORT_DONE: { en: "Starter products added.", hi: "स्टार्टर प्रोडक्ट जोड़ दिए गए।" },
  TRY_ASKING: { en: "Try asking", hi: "पूछकर देखें" },
  BUSINESS_TYPE: { en: "Business type", hi: "व्यवसाय प्रकार" },
  BUSINESS_TYPE_DESC: {
    en: "We personalize invoices, products, and AI suggestions for your MSME segment.",
    hi: "हम आपके MSME सेगमेंट के अनुसार इनवॉइस, प्रोडक्ट और AI सुझाव अनुकूलित करते हैं।",
  },
  SAVED: { en: "Business type updated.", hi: "व्यवसाय प्रकार अपडेट हो गया।" },
} as const;

export const ASSISTANT_QUERY_PARAM = "q";

export const LOGIN_COPY = {
  SUITE_TAGLINE: { en: "AI BUSINESS MANAGER FOR INDIAN MSMES", hi: "भारतीय MSME के लिए AI बिज़नेस मैनेजर" },
  HERO_PRIMARY: { en: "Every MSME.", hi: "हर MSME।" },
  HERO_ACCENT: { en: "One smart platform.", hi: "एक स्मार्ट प्लेटफॉर्म।" },
  HERO_SUB: {
    en: "Pick your business type — we adapt invoices, GST, and collections to how you work.",
    hi: "अपना व्यवसाय चुनें — हम इनवॉइस, GST और कलेक्शन आपके काम के अनुसार अनुकूलित करते हैं।",
  },
  BUILT_FOR: {
    en: "From kirana to factory — built for how India actually does business.",
    hi: "किराना से फैक्ट्री तक — भारत जैसा व्यवसाय करता है, उसी के लिए।",
  },
  WELCOME: { en: "Welcome back", hi: "वापसी पर स्वागत है" },
  SUBTITLE: { en: "Sign in to your workspace", hi: "अपने वर्कस्पेस में साइन इन करें" },
  EMAIL_LABEL: { en: "Email or username", hi: "ईमेल या यूज़रनेम" },
  EMAIL_PLACEHOLDER: { en: "you@yourshop.in", hi: "you@yourshop.in" },
  REMEMBER: { en: "Remember me", hi: "मुझे याद रखें" },
  SIGN_IN: { en: "Sign in", hi: "साइन इन" },
  SIGNING_IN: { en: "Signing in…", hi: "साइन इन हो रहा है…" },
  OR_CONTINUE: { en: "or continue with", hi: "या इससे जारी रखें" },
  NEW_HERE: { en: "New here?", hi: "नए हैं?" },
  START_FREE: { en: "Start free", hi: "मुफ़्त शुरू करें" },
  YOUR_BUSINESS: { en: "Your business type", hi: "आपका व्यवसाय प्रकार" },
} as const;

export const ONBOARDING_COPY = {
  TITLE: "Welcome to KuberAIQ",
  STEP_COMPANY: "Business details",
  STEP_SEGMENT: "Your business type",
  STEP_SEGMENT_DESC: "We picked this from login — change it if needed. This personalizes your workspace.",
  STEP_COMPLIANCE: "Compliance profile",
  STEP_PAYMENTS: "Payments (optional)",
  STEP_COMPANY_DESC: "We use your GSTIN for tax-compliant invoices.",
  STEP_COMPLIANCE_DESC: "Personalize your compliance calendar — takes under a minute.",
  STEP_PAYMENTS_DESC: "Add UPI for QR codes on invoices and enable auto-reminders.",
  CONTINUE: "Continue",
  SKIP: "Skip for now",
  FINISH: "Go to dashboard",
  PROGRESS: (step: number, total: number) => `Step ${step} of ${total}`,
} as const;

export const SUPPORT_EMAIL = "support@kuberaiq.com";
export const PRIVACY_EMAIL = "privacy@kuberaiq.com";
export const SECURITY_EMAIL = "security@kuberaiq.com";

export const LEGAL_COPY = {
  TERMS_TITLE: "Terms of Service",
  PRIVACY_TITLE: "Privacy Policy",
  LAST_UPDATED: "Last updated: 6 June 2026",
  FOOTER_TERMS: "Terms",
  FOOTER_PRIVACY: "Privacy",
  AGREE_LABEL: "I agree to the Terms of Service and Privacy Policy",
  TERMS_CONTACT: `Questions about these Terms: ${SUPPORT_EMAIL}.`,
  PRIVACY_CONTACT: `Data protection queries: ${PRIVACY_EMAIL}. We will respond within timelines required under applicable law.`,
  SECURITY_CONTACT: `Report suspected breaches to ${SECURITY_EMAIL}.`,
} as const;
