export const APP_NAME = "VyaparAI";
export const DEMO_LOGIN_EMAIL = "owner@demo.vyaparai.com";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "vyaparai_access_token",
  REFRESH_TOKEN: "vyaparai_refresh_token",
  USER: "vyaparai_user",
} as const;

export const ROUTES = {
  HOME: "/",
  LOGIN: "/login",
  DASHBOARD: "/dashboard",
  INVOICES: "/invoices",
  INVOICES_NEW: "/invoices/new",
  CUSTOMERS: "/customers",
  COLLECTIONS: "/collections",
  ASSISTANT: "/assistant",
  SETTINGS: "/settings",
} as const;

export const API_PATHS = {
  MOCK_LOGIN: "/auth/mock-login",
  ME: "/auth/me",
  REFRESH: "/auth/refresh",
  LOGOUT: "/auth/logout",
  CUSTOMERS: "/customers",
  INVOICES: "/invoices",
  COLLECTIONS_OVERDUE: "/collections/overdue",
  COLLECTIONS_DASHBOARD: "/collections/dashboard",
  DASHBOARD: "/dashboard",
  AI_CHAT: "/ai/chat",
} as const;

export const QUERY_KEYS = {
  ME: ["auth", "me"] as const,
  DASHBOARD: (from?: string, to?: string) => ["dashboard", from, to] as const,
  INVOICES: (params?: object) => ["invoices", params] as const,
  INVOICE: (id: string) => ["invoices", id] as const,
  CUSTOMERS: (params?: object) => ["customers", params] as const,
  CUSTOMER: (id: string) => ["customers", id] as const,
  COLLECTIONS_OVERDUE: (params?: object) => ["collections", "overdue", params] as const,
  COLLECTIONS_DASHBOARD: ["collections", "dashboard"] as const,
  AI_SESSION: (id: string) => ["ai", "session", id] as const,
} as const;

export const NAV_ITEMS = [
  { href: ROUTES.DASHBOARD, label: "Dashboard", icon: "LayoutDashboard" },
  { href: ROUTES.INVOICES, label: "Invoices", icon: "FileText" },
  { href: ROUTES.CUSTOMERS, label: "Customers", icon: "Users" },
  { href: ROUTES.COLLECTIONS, label: "Collections", icon: "IndianRupee" },
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
  [ROUTES.CUSTOMERS]: "Customers",
  [ROUTES.COLLECTIONS]: "Collections",
  [ROUTES.ASSISTANT]: "AI Assistant",
  [ROUTES.SETTINGS]: "Settings",
};

export const DEFAULT_PAGE_SIZE = 20;

export const ASSISTANT_CHANNEL = "web";
