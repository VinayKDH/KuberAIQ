export const APP_NAME = "KuberAIQ";
export const DEMO_LOGIN_EMAIL = "owner@demo.kuberaiq.com";

/** Public production URLs (custom domain; overridden at Docker build via NEXT_PUBLIC_*). */
export const PUBLIC_WEB_URL =
  process.env.NEXT_PUBLIC_WEB_URL ?? "https://www.kuberaiq.com";
export const PUBLIC_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.kuberaiq.com";
export const PUBLIC_APEX_DOMAIN = "kuberaiq.com";
export const LOCAL_API_URL = "http://localhost:8000";

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
  SETTINGS: "/settings",
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
  DASHBOARD: "/dashboard",
  COMPLIANCE_DASHBOARD: "/compliance/dashboard",
  COMPLIANCE_OBLIGATIONS: "/compliance/obligations",
  COMPLIANCE_CALENDAR: "/compliance/calendar",
  COMPLIANCE_COMPLETE: (id: string) => `/compliance/obligations/${id}/complete` as const,
  COMPLIANCE_PROFILE: "/compliance/profile",
  COMPLIANCE_ALERTS_PREVIEW: "/compliance/alerts/preview",
  AI_CHAT: "/ai/chat",
  AI_CONFIRM: "/ai/confirm",
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
  COMPLIANCE: ["compliance", "dashboard"] as const,
  COMPLIANCE_OBLIGATIONS: ["compliance", "obligations"] as const,
  COMPLIANCE_CALENDAR: (days?: number) => ["compliance", "calendar", days] as const,
} as const;

export const NAV_ITEMS = [
  { href: ROUTES.DASHBOARD, label: "Dashboard", icon: "LayoutDashboard" },
  { href: ROUTES.INVOICES, label: "Invoices", icon: "FileText" },
  { href: ROUTES.QUOTATIONS, label: "Quotations", icon: "ClipboardList" },
  { href: ROUTES.PRODUCTS, label: "Products", icon: "Package" },
  { href: ROUTES.CUSTOMERS, label: "Customers", icon: "Users" },
  { href: ROUTES.COLLECTIONS, label: "Collections", icon: "IndianRupee" },
  { href: ROUTES.COMPLIANCE, label: "Compliance", icon: "ShieldCheck" },
  { href: ROUTES.ASSISTANT, label: "Assistant", icon: "Bot" },
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
  [ROUTES.ASSISTANT]: "AI Assistant",
  [ROUTES.SETTINGS]: "Settings",
};

export const DEFAULT_PAGE_SIZE = 20;
export const DEFAULT_DUE_DAYS = 15;

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

export const SUBSCRIPTION_PAGE = {
  TITLE: "Activate your subscription",
  DESCRIPTION: "Complete payment to set up your business workspace. Each account gets its own isolated data.",
  PLAN_NAME: "KuberAIQ Starter",
  BILLING_CYCLE: "per month · billed monthly",
  PAY_CTA: "Pay with Razorpay",
  MOCK_PAY_CTA: "Activate (demo — no charge)",
  PAYING: "Processing…",
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

export const ONBOARDING_COPY = {
  TITLE: "Welcome to KuberAIQ",
  STEP_COMPANY: "Business details",
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

export const LEGAL_COPY = {
  TERMS_TITLE: "Terms of Service",
  PRIVACY_TITLE: "Privacy Policy",
  LAST_UPDATED: "Last updated: 6 June 2026",
  FOOTER_TERMS: "Terms",
  FOOTER_PRIVACY: "Privacy",
  AGREE_LABEL: "I agree to the Terms of Service and Privacy Policy",
} as const;
