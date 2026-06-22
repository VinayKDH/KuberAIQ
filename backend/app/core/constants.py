"""Central registry of static values (per project convention: no magic literals).

Every fixed string, number, label, or enum-like value used across the codebase lives
here so behaviour is consistent and changes happen in one place.
"""
from __future__ import annotations

import re
from decimal import Decimal

# --- App metadata ----------------------------------------------------------
APP_NAME = "KuberAIQ"
APP_TAGLINE = "AI Business Manager for Indian MSMEs"
API_V1_PREFIX = "/api/v1"

# --- Currency / locale -----------------------------------------------------
CURRENCY_CODE = "INR"
CURRENCY_SYMBOL = "₹"
PDF_CURRENCY_PREFIX = "Rs. "
MONEY_QUANTIZE = Decimal("0.01")
QUANTITY_QUANTIZE = Decimal("0.001")
DEFAULT_TIMEZONE = "Asia/Kolkata"

# --- GST rules -------------------------------------------------------------
ALLOWED_GST_RATES: tuple[Decimal, ...] = (
    Decimal("0"),
    Decimal("5"),
    Decimal("12"),
    Decimal("18"),
    Decimal("28"),
)
# Common HSN/SAC → default GST rate (exact 4-digit codes)
HSN_EXACT_GST_RATES: dict[str, str] = {
    "0401": "0",   # fresh milk
    "0402": "5",   # milk products (khoya, milk powder)
    "0403": "5",   # yoghurt, buttermilk
    "0405": "12",  # butter, ghee
    "0406": "5",   # paneer, cheese
    "0407": "0",   # eggs
    "0409": "5",   # honey
    "0701": "0",   # fresh vegetables
    "0713": "0",   # pulses
    "0803": "0",   # fresh fruits
    "0901": "5",   # coffee
    "0902": "5",   # tea
    "0910": "5",   # spices
    "1001": "0",   # wheat
    "1006": "0",   # rice
    "1209": "0",   # seeds
    "1507": "5",   # edible oil
    "1701": "5",   # sugar
    "1902": "18",  # pasta / noodles
    "1905": "18",  # biscuits (also 5% for bread — catalogue uses 18% for snacks)
    "2103": "12",  # sauces / pickles
    "2105": "18",  # ice cream
    "2106": "18",  # food preparations
    "2201": "18",  # mineral water
    "2202": "28",  # soft drinks
    "2501": "0",   # salt
    "2517": "5",   # sand / aggregate
    "2523": "28",  # cement
    "2710": "18",  # petroleum products
    "3004": "12",  # medicaments
    "3102": "5",   # fertilizer
    "3209": "28",  # paint
    "3214": "18",  # waterproofing
    "3305": "18",  # hair / cosmetics
    "3401": "18",  # soap / detergent
    "3506": "18",  # adhesives
    "3808": "18",  # disinfectants / pesticides
    "3824": "28",  # ready-mix concrete
    "3917": "18",  # plastic pipes / conduit
    "3919": "18",  # packaging tape
    "3922": "18",  # bathroom accessories
    "3923": "18",  # plastic articles
    "3925": "18",  # water tanks
    "4011": "28",  # tyres
    "4013": "28",  # tubes
    "4016": "18",  # rubber articles
    "4412": "18",  # plywood
    "4819": "12",  # corrugated boxes
    "4820": "12",  # stationery paper
    "5208": "5",   # cotton fabric
    "5407": "12",  # synthetic fabric
    "6109": "5",   # garments
    "6204": "5",   # women's / ethnic wear
    "6302": "5",   # towels / linen
    "6403": "5",   # footwear
    "6506": "18",  # safety headgear
    "6802": "28",  # marble / granite
    "6901": "12",  # bricks
    "6907": "28",  # ceramic tiles
    "6910": "18",  # sanitaryware
    "7005": "18",  # glass
    "7210": "18",  # roofing sheets
    "7214": "18",  # steel bars
    "7216": "18",  # structural steel
    "7217": "18",  # wire
    "7219": "18",  # stainless steel
    "7318": "18",  # fasteners
    "7408": "18",  # copper wire
    "7604": "18",  # aluminium profiles
    "7606": "18",  # aluminium sheets
    "8205": "18",  # hand tools
    "8311": "18",  # welding consumables
    "8413": "18",  # pumps
    "8414": "18",  # fans
    "8415": "18",  # air conditioners
    "8418": "18",  # refrigerators
    "8424": "12",  # sprinklers / irrigation
    "8443": "18",  # printers
    "8450": "18",  # washing machines
    "8467": "18",  # power tools
    "8471": "18",  # computers
    "8481": "18",  # taps / valves
    "8504": "18",  # inverters
    "8507": "18",  # batteries
    "8516": "18",  # heaters / microwaves
    "8517": "18",  # telecom equipment
    "8528": "18",  # TVs / monitors
    "8536": "18",  # switches
    "8539": "18",  # lamps / bulbs
    "8544": "18",  # cables
    "8708": "28",  # auto parts
    "9015": "18",  # measuring instruments
    "9032": "18",  # stabilizers
    "9403": "18",  # furniture
    "9608": "12",  # pens
    "9619": "12",  # sanitary napkins
    "9963": "18",  # SAC — restaurant / hotel
    "9965": "18",  # SAC — freight
    "9971": "18",  # SAC — insurance
    "9973": "18",  # SAC — equipment rental
    "9983": "18",  # SAC — professional services
    "9987": "18",  # SAC — maintenance services
    "9989": "18",  # SAC — printing
    "9992": "18",  # SAC — education / training
    "9997": "18",  # SAC — beauty / fitness
}
# Prefix fallbacks — longest match wins (stored longest-first)
HSN_PREFIX_GST_RATES: tuple[tuple[str, str], ...] = (
    ("9989", "18"),
    ("9997", "18"),
    ("9992", "18"),
    ("9973", "18"),
    ("9971", "18"),
    ("9965", "18"),
    ("9987", "18"),
    ("9983", "18"),
    ("9963", "18"),
    ("0406", "5"),
    ("0402", "5"),
    ("07", "0"),    # vegetables
    ("08", "0"),    # fruits
    ("09", "5"),    # coffee, tea, spices
    ("10", "0"),    # cereals
    ("12", "0"),    # oil seeds
    ("15", "5"),    # fats / oils
    ("19", "18"),   # prepared foods
    ("22", "18"),   # beverages (exact codes override)
    ("25", "28"),   # mineral products
    ("32", "18"),   # paints / chemicals
    ("39", "18"),   # plastics
    ("40", "28"),   # rubber
    ("44", "18"),   # wood
    ("48", "12"),   # paper
    ("52", "5"),    # cotton
    ("61", "5"),    # garments
    ("62", "5"),    # apparel
    ("63", "5"),    # made-up textiles
    ("64", "5"),    # footwear
    ("68", "28"),   # stone
    ("69", "28"),   # ceramics
    ("72", "18"),   # iron & steel
    ("76", "18"),   # aluminium
    ("82", "18"),   # tools
    ("84", "18"),   # machinery
    ("85", "18"),   # electronics
    ("87", "28"),   # vehicles / parts
    ("94", "18"),   # furniture
    ("04", "5"),    # dairy chapter
)
# Product-name hints live in app.core.gst_product_catalog.GST_PRODUCT_CATALOG
DEFAULT_PRODUCT_GST_RATE = Decimal("18")
GST_TOLERANCE = Decimal("0.02")  # acceptable rounding delta when validating totals
GSTIN_LENGTH = 15
GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

# --- Phone -----------------------------------------------------------------
INDIA_PHONE_REGEX = r"^[6-9]\d{9}$"
INDIA_COUNTRY_CODE = "91"

# --- Invoice numbering -----------------------------------------------------
DEFAULT_INVOICE_PREFIX = "INV"
DEFAULT_QUOTATION_PREFIX = "QT"
DEFAULT_CREDIT_NOTE_PREFIX = "CN"
INVOICE_NUMBER_PAD = 4  # INV/2025-26/0042
FINANCIAL_YEAR_START_MONTH = 4  # April

# --- Document types --------------------------------------------------------
DOCUMENT_TYPE_INVOICE = "INVOICE"
DOCUMENT_TYPE_CREDIT_NOTE = "CREDIT_NOTE"

# --- GSTR export -----------------------------------------------------------
GSTR_B2C_LARGE_THRESHOLD = Decimal("250000")  # ₹2.5L inter-state B2C large invoice threshold
GSTR_REPORT_MAX_INVOICES = 10000
GSTR1_DISCLAIMER = (
    "MVP export derived from issued invoices. Does not include amendments, "
    "credit/debit notes in portal format, or Table 12/13 details. Verify on GST portal."
)
GSTR3B_DISCLAIMER = (
    "MVP outward-supply summary only. Input tax credit (ITC) and payment "
    "liability must be reconciled separately on the GST portal."
)

# --- Defaults --------------------------------------------------------------
DEFAULT_DUE_DAYS = 15
DEFAULT_UNIT = "NOS"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# --- Collections -----------------------------------------------------------
REMINDER_COOLDOWN_HOURS = 48

# --- Billing / subscriptions -----------------------------------------------
SUBSCRIPTION_PLAN_STARTER = "starter_monthly"
SUBSCRIPTION_PLAN_STARTER_LABEL = "KuberAIQ Starter"
SUBSCRIPTION_STARTER_AMOUNT_PAISE = 99900  # ₹999/month
SUBSCRIPTION_PERIOD_DAYS = 30
SUBSCRIPTION_EXPIRY_JOB_HOUR = 1
SUBSCRIPTION_EXPIRY_JOB_MINUTE = 0
RAZORPAY_WEBHOOK_PATH = "/api/v1/billing/webhooks/razorpay"
RAZORPAY_INVOICE_WEBHOOK_PATH = "/api/v1/payments/webhooks/razorpay"
RAZORPAY_API_BASE_URL = "https://api.razorpay.com/v1"
RAZORPAY_CHECKOUT_SCRIPT_URL = "https://checkout.razorpay.com/v1/checkout.js"
RAZORPAY_INVOICE_REFERENCE_PREFIX = "inv-"
RAZORPAY_PAYMENT_REFERENCE_PREFIX = "rzp:"
RAZORPAY_INVOICE_WEBHOOK_EVENTS: tuple[str, ...] = ("payment.captured", "payment_link.paid")
PAYMENT_SUMMARY_RECENT_LIMIT = 10
PAYMENT_RECONCILIATION_AMOUNT_TOLERANCE = 1  # rupees
UPI_DEEP_LINK_STUB_NOTE = "UPI payment — confirm amount and record if not auto-matched"

# --- Inventory alerts ------------------------------------------------------
LOW_STOCK_THRESHOLD_DEFAULT = 10
STOCK_REFERENCE_MANUAL = "manual"
STOCK_ADJUSTMENT_REASONS: tuple[str, ...] = (
    "Purchase",
    "Opening stock",
    "Stock correction",
    "Damaged / expired",
    "Return from customer",
    "Other",
)

# --- CA workspace ----------------------------------------------------------
CA_TASK_STATUS_PENDING = "pending"
CA_TASK_STATUS_DONE = "done"
CA_TASK_STATUS_CANCELLED = "cancelled"
CA_FILING_EXPORT_CSV_HEADERS: tuple[str, ...] = (
    "company_name",
    "gstin",
    "obligation_id",
    "title",
    "due_date",
    "status",
    "period_key",
)

# --- Auth / security -------------------------------------------------------
ACCESS_TOKEN_TTL_MINUTES = 15
REFRESH_TOKEN_TTL_DAYS = 7
JWT_ALGORITHM = "HS256"  # RS256 in production with Key Vault keys

# --- OAuth providers -------------------------------------------------------
OAUTH_PROVIDER_MICROSOFT = "microsoft"
OAUTH_PROVIDER_GOOGLE = "google"
GOOGLE_OAUTH_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_OAUTH_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_OAUTH_ISSUERS: tuple[str, ...] = ("https://accounts.google.com", "accounts.google.com")
GOOGLE_OAUTH_SCOPES = "openid email profile"
AUTH_SCHEME = "Bearer"

# --- Rate limits (requests per window) -------------------------------------
RATE_LIMIT_DEFAULT_PER_MIN = 300
RATE_LIMIT_IP_PER_MIN = 100
RATE_LIMIT_AUTH_PER_MIN = 10
RATE_LIMIT_AI_PER_MIN = 20

# --- Security headers ------------------------------------------------------
SECURITY_HEADER_REFERRER = "strict-origin-when-cross-origin"
SECURITY_HEADER_CSP = "default-src 'none'; frame-ancestors 'none'"
SECURITY_HEADER_PERMISSIONS_POLICY = "geolocation=(), camera=()"

# --- AI --------------------------------------------------------------------
AI_MAX_MESSAGE_LEN = 2000
AI_HISTORY_TURNS = 10
AI_RESPONSE_MAX_LEN = 1000
AI_MAX_TOKENS_CLASSIFY = 256
AI_MAX_TOKENS_EXTRACT = 512
AI_MAX_TOKENS_GENERATE = 1024
AI_SOFT_TOKEN_BUDGET_MONTHLY = 200000

AI_CUSTOMER_NAME_STOP_WORDS = frozenset(
    {
        "of",
        "the",
        "a",
        "an",
        "for",
        "with",
        "and",
        "to",
        "at",
        "in",
        "on",
        "item",
        "items",
        "product",
        "products",
    }
)

AI_INVOICE_UNIT_ALIASES: dict[str, str] = {
    "bag": "BAG",
    "bags": "BAG",
    "kg": "KG",
    "kgs": "KG",
    "kilo": "KG",
    "kilos": "KG",
    "nos": "NOS",
    "no": "NOS",
    "unit": "NOS",
    "units": "NOS",
    "pc": "PCS",
    "pcs": "PCS",
    "piece": "PCS",
    "pieces": "PCS",
    "liter": "LTR",
    "liters": "LTR",
    "litre": "LTR",
    "litres": "LTR",
    "ltr": "LTR",
}

# Skip 10-digit numbers immediately preceded by price markers (not substrings like "rs" in "Person").
AI_PHONE_PRICE_PREFIX_RE = re.compile(
    r"(?:@|₹|\bat\s|\brate\s|\brs\.?\s*)$",
    re.I,
)

# Price markers before amounts — word-boundary aware (avoids "Traders" → rs + phone digits).
AI_PRICE_AMOUNT_RE = re.compile(
    r"(?:@|₹|\bat\s|\brate\s|\brs\.?\s*)(\d+(?:\.\d+)?)",
    re.I,
)

AI_INVOICE_LINE_ITEM_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)?)\s*"
    r"(bags?|kg|kgs?|nos|units?|pcs?|pieces?|liters?|litres?|ltr|litre)\s+"
    r"(?:of\s+)?(.+)$",
    re.I,
)

# --- Error codes (stable, client-facing) -----------------------------------
class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL_ERROR"
    GSTIN_INVALID = "GSTIN_INVALID"
    GSTIN_CONFLICT = "GSTIN_CONFLICT"
    PHONE_INVALID = "PHONE_INVALID"
    INVOICE_NOT_EDITABLE = "INVOICE_NOT_EDITABLE"
    INVOICE_HAS_PAYMENTS = "INVOICE_HAS_PAYMENTS"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    PAYMENT_EXCEEDS_DUE = "PAYMENT_EXCEEDS_DUE"
    DUPLICATE = "DUPLICATE"


# --- Audit actions ---------------------------------------------------------
class AuditAction:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    CANCEL = "CANCEL"
    ISSUE = "ISSUE"
    DELETE = "DELETE"
    PAYMENT = "PAYMENT"
    PAYMENT_REVERSE = "PAYMENT_REVERSE"
    REMINDER_SENT = "REMINDER_SENT"
    COMPLIANCE_ALERT_SENT = "COMPLIANCE_ALERT_SENT"
    CONVERT = "CONVERT"
    AI_TOOL_CALL = "AI_TOOL_CALL"


# --- Entity type labels (for audit logs) -----------------------------------
class EntityType:
    INVOICE = "invoice"
    CUSTOMER = "customer"
    PAYMENT = "payment"
    REMINDER = "reminder"
    COMPANY = "company"
    USER = "user"
    PRODUCT = "product"
    QUOTATION = "quotation"
    CREDIT_NOTE = "credit_note"


# --- Admin portal ----------------------------------------------------------
ADMIN_API_KEY_HEADER = "X-Admin-Api-Key"
ADMIN_ENTITY_TYPE_COMPANY = "company"
ADMIN_ACTION_SUSPEND = "suspend"
ADMIN_ACTION_ACTIVATE = "activate"
ADMIN_DEMO_RESET_ALLOWED_ENVIRONMENTS = frozenset({"local", "dev"})

# --- Health ----------------------------------------------------------------
HEALTH_LIVE_PATH = "/health"
HEALTH_READY_PATH = "/health/ready"
HEALTH_METRICS_PATH = "/health/metrics"

# --- Demo seed (local mode) ------------------------------------------------
DEMO_COMPANY_NAME = "Demo Traders Pvt Ltd"
# Synthetic GSTIN reserved for demo seed — must not collide with real MSME registrations.
DEMO_COMPANY_GSTIN = "99AAAAA0000A1ZR"
DEMO_COMPANY_STATE = "99"
DEMO_COMPANY_ADDRESS = "MIDC, Pune, Maharashtra"
DEMO_USER_EMAIL = "owner@demo.kuberaiq.com"
DEMO_USER_NAME = "Demo Owner"
LEGACY_DEMO_USER_EMAIL = "owner@demo.vyaparai.com"
DEMO_COMPANY_UPI_ID = "demotraders@upi"
DEMO_COMPANY_UPI_PAYEE_NAME = DEMO_COMPANY_NAME
DEMO_COMPANY_ENTITY_TYPE = "PRIVATE_LIMITED"
DEMO_COMPANY_TURNOVER_BAND = "_100L_500L"
DEMO_COMPANY_GSTR1_FREQUENCY = "MONTHLY"
DEMO_COMPANY_EMPLOYEE_COUNT = 8
DEMO_COMPANY_UDYAM_NUMBER = "UDYAM-MH-27-0123456"
DEMO_COMPANY_HAS_TDS = False
DEMO_COMPANY_AUTO_REMINDERS = True
DEMO_COMPANY_REMINDER_LANGUAGE = "en"

# --- CA persona -----------------------------------------------------------
CA_EMAIL_DOMAIN = "@ca.kuberaiq.com"
DEMO_CA_EMAIL = "ca@demo.kuberaiq.com"
DEMO_CA_NAME = "Demo CA"
DEMO_CA_FIRM_NAME = "Demo & Associates"
DEMO_CA_USER_ID = "00000000-0000-4000-8000-000000000003"
CA_INVITE_ALREADY_EXISTS = "This CA is already invited or assigned to your company"
CA_INVITE_NOT_FOUND = "CA assignment not found"
CA_NOT_ASSIGNED = "You are not assigned to this client"
CA_CONTEXT_REQUIRED = "Select a client to view compliance data"

# --- Aging buckets ---------------------------------------------------------
AGING_BUCKETS: tuple[str, ...] = ("0-30", "31-60", "61-90", "90+")

# --- Compliance (GST / e-invoice) ------------------------------------------
E_INVOICE_TURNOVER_THRESHOLD = Decimal("1000000")  # ₹10 lakh — Apr 2025 threshold
E_INVOICE_IRN_MAX_AGE_DAYS = 30
COMPLIANCE_GSTR1_DUE_DAY = 11
COMPLIANCE_GSTR3B_DUE_DAY = 20
COMPLIANCE_TDS_DUE_DAY = 7
COMPLIANCE_DEADLINE_LOOKAHEAD_DAYS = 45
COMPLIANCE_STATUS_UPCOMING = "UPCOMING"
COMPLIANCE_STATUS_DUE_SOON = "DUE_SOON"
COMPLIANCE_STATUS_OVERDUE = "OVERDUE"
COMPLIANCE_DISCLAIMER = (
    "Compliance dates are indicative for planning. Verify on the GST portal before filing."
)

# --- Compliance WhatsApp alerts --------------------------------------------
COMPLIANCE_ALERT_FALLBACK_PHONE = "919999999999"
COMPLIANCE_ALERT_MESSAGE_PREFIX = "KuberAIQ compliance reminder:"
COMPLIANCE_ENTITY_TYPE_DEFAULT = "PROPRIETORSHIP"
COMPLIANCE_ENTITY_TYPES: tuple[str, ...] = (
    "PROPRIETORSHIP",
    "PARTNERSHIP",
    "LLP",
    "PRIVATE_LIMITED",
    "PUBLIC_LIMITED",
)
COMPLIANCE_TURNOVER_BANDS: tuple[str, ...] = (
    "BELOW_40L",
    "_40L_100L",
    "_100L_500L",
    "ABOVE_500L",
)
COMPLIANCE_TURNOVER_BAND_ORDER: tuple[str, ...] = COMPLIANCE_TURNOVER_BANDS
COMPLIANCE_GSTR1_FREQUENCY_MONTHLY = "MONTHLY"
COMPLIANCE_GSTR1_FREQUENCY_QUARTERLY = "QUARTERLY"
COMPLIANCE_GSTR1_FREQUENCIES: tuple[str, ...] = (
    COMPLIANCE_GSTR1_FREQUENCY_MONTHLY,
    COMPLIANCE_GSTR1_FREQUENCY_QUARTERLY,
)
MSME_SEGMENT_IDS: tuple[str, ...] = (
    "kirana",
    "trader",
    "manufacturing",
    "services",
    "construction",
    "food",
)
RECURRING_INVOICE_FREQUENCIES: tuple[str, ...] = ("MONTHLY", "WEEKLY", "DAILY")
CA_OVERDUE_ALERT_THRESHOLD = 10_000
CA_FILING_DUE_SOON_DAYS = 7
CA_FILING_CHECKLIST_IDS: tuple[str, ...] = ("gst_gstr1", "gst_gstr3b", "it_itr")
CA_HEALTH_SCORE_AT_RISK = 70
COMPLIANCE_OBLIGATION_STATUS_PENDING = "PENDING"
COMPLIANCE_OBLIGATION_STATUS_COMPLETED = "COMPLETED"
COMPLIANCE_OBLIGATION_STATUS_OVERDUE = "OVERDUE"
COMPLIANCE_OBLIGATION_STATUS_NOT_APPLICABLE = "NOT_APPLICABLE"
COMPLIANCE_OBLIGATION_STATUS_SKIPPED = "SKIPPED"
COMPLIANCE_OBLIGATION_STATUSES: tuple[str, ...] = (
    COMPLIANCE_OBLIGATION_STATUS_PENDING,
    COMPLIANCE_OBLIGATION_STATUS_COMPLETED,
    COMPLIANCE_OBLIGATION_STATUS_OVERDUE,
    COMPLIANCE_OBLIGATION_STATUS_NOT_APPLICABLE,
    COMPLIANCE_OBLIGATION_STATUS_SKIPPED,
)
COMPLIANCE_CATEGORIES: tuple[str, ...] = ("GST", "INCOME_TAX", "LABOUR", "MCA", "OTHER")
COMPLIANCE_GSTR9_DUE_MONTH = 12
COMPLIANCE_GSTR9_DUE_DAY = 31
COMPLIANCE_ITR_DUE_MONTH = 7
COMPLIANCE_ITR_DUE_DAY = 31
COMPLIANCE_MCA_DUE_MONTH = 9
COMPLIANCE_MCA_DUE_DAY = 30
COMPLIANCE_ADVANCE_TAX_DAYS: tuple[tuple[int, int], ...] = (
    (6, 15),
    (9, 15),
    (12, 15),
    (3, 15),
)
COMPLIANCE_PF_DUE_DAY = 15
COMPLIANCE_ESI_DUE_DAY = 15
COMPLIANCE_PROF_TAX_DUE_DAY = 20
COMPLIANCE_SHOP_EST_DUE_MONTH = 3
COMPLIANCE_SHOP_EST_DUE_DAY = 31
COMPLIANCE_CALENDAR_DEFAULT_DAYS = 90
COMPLIANCE_DUE_SOON_DAYS = 3
COMPLIANCE_HEALTH_SCORE_COMPLETE = 100
COMPLIANCE_HEALTH_SCORE_OVERDUE_PENALTY = 15
COMPLIANCE_HEALTH_SCORE_DUE_SOON_PENALTY = 5

# --- Cashflow forecast -----------------------------------------------------
CASHFLOW_FORECAST_DAYS = 30
CASHFLOW_BUFFER_DEFAULT = Decimal("50000")
CASHFLOW_ALERT_DUE_SOON_DAYS = 7

# --- Sales analytics -------------------------------------------------------
TOP_PRODUCTS_LIMIT = 5
TOP_CUSTOMERS_LIMIT = 5

# --- AI routes / intents ---------------------------------------------------
class AiRoute:
    INVOICE = "invoice"
    COLLECTIONS = "collections"
    DASHBOARD = "dashboard"
    CUSTOMER = "customer"
    HELP = "help"
    CLARIFY = "clarify"


AI_ROUTE_HELP_KEYWORDS = (
    "help",
    "what can you do",
    "how do i",
    "commands",
    "hi",
    "hello",
    "hey",
    "namaste",
    "good morning",
    "good evening",
)

AI_ROUTE_REMINDER_KEYWORDS = (
    "send reminder",
    "remind all",
    "bulk remind",
    "reminders to all",
    "whatsapp reminder",
)

AI_ROUTE_INVOICE_KEYWORDS = (
    "create invoice",
    "make invoice",
    "new invoice",
    "generate invoice",
    "raise invoice",
    "bill for",
    "invoice for",
    "bill to",
    "invoice to",
    "sell ",
    "with paneer",
    "with khoya",
)

AI_ROUTE_DASHBOARD_KEYWORDS = (
    "revenue",
    "dashboard",
    "summarize",
    "summary",
    "cashflow",
    "cash flow",
    "aging",
    "business overview",
    "how is business",
)

AI_ROUTE_COLLECTIONS_KEYWORDS = (
    "overdue",
    "unpaid",
    "not paid",
    "pending",
    "outstanding",
    "due amount",
    "money pending",
    "collect",
    "payment due",
    "amount due",
    "who owes",
    "show invoices",
    "kitna baki",
    "baki hai",
    "udhaar",
    "payment pending",
    "dues",
    "recovery",
)

AI_ROUTE_CUSTOMER_KEYWORDS = (
    "customer",
    "client",
    "trader",
    "add customer",
    "create customer",
    "new customer",
    "find customer",
)

AI_HELP_SUGGESTED_ACTIONS = (
    {"label": "Pending collections", "value": "How much money is pending?"},
    {"label": "Overdue invoices", "value": "Show overdue invoices"},
    {"label": "Business summary", "value": "Summarize my dashboard"},
    {"label": "Create invoice", "value": "Create invoice for a customer"},
)

AI_CLARIFY_SUGGESTED_ACTIONS = AI_HELP_SUGGESTED_ACTIONS

AI_COMPLIANCE_HINT = (
    "GST filing and compliance calendars are in the Compliance section. "
    "I can still help with invoices, collections, and your business summary here."
)

class AiIntent:
    CREATE_INVOICE = "create_invoice"
    LIST_OVERDUE = "list_overdue"
    LIST_UNPAID = "list_unpaid"
    SEND_REMINDER = "send_reminder"
    BULK_SEND_REMINDERS = "bulk_send_reminders"
    GET_DASHBOARD = "get_dashboard"
    FIND_CUSTOMER = "find_customer"
    CREATE_CUSTOMER = "create_customer"
    CREATE_CUSTOMER_AND_INVOICE = "create_customer_and_invoice"
    CLARIFY = "clarify"


class AiAwaiting:
    """Slots the copilot is waiting to fill from the user's next message."""

    CUSTOMER_NAME = "customer_name"
    CUSTOMER_PHONE = "customer_phone"
    INVOICE_CUSTOMER = "invoice_customer"
    CREATE_MISSING_CUSTOMER = "create_missing_customer"


AI_CONTEXT_CONFIRM_WORDS = frozenset(
    {"yes", "y", "confirm", "ok", "okay", "proceed", "go ahead", "sure", "do it"}
)

AI_CONTEXT_CANCEL_WORDS = frozenset({"no", "n", "cancel", "stop", "abort", "never mind"})

AI_CONTEXT_PRONOUN_PHRASES = (
    "them",
    "that customer",
    "same customer",
    "this customer",
    "for him",
    "for her",
    "for them",
    "that one",
    "same one",
)

AI_CONTEXT_REMINDER_FOLLOW_UPS = (
    "send reminder",
    "remind them",
    "send it",
    "whatsapp them",
    "remind that customer",
)

AI_CONTEXT_INVOICE_FOLLOW_UPS = (
    "invoice them",
    "bill them",
    "create invoice for them",
    "invoice that customer",
    "bill that customer",
)

AI_CONTEXT_CREATE_CUSTOMER_AFFIRMATIONS = (
    "create them",
    "add them",
    "create customer",
    "add customer",
    "yes create",
    "yes add",
    "create first",
    "add first",
)


# --- PDF / storage ---------------------------------------------------------
PDF_SIGNED_URL_TTL_SECONDS = 3600
BLOB_INVOICE_PREFIX = "invoices"
PDF_BRAND_COLOR = "#1e3a5f"
PDF_ACCENT_COLOR = "#2563eb"
PDF_MUTED_COLOR = "#64748b"
PDF_BORDER_COLOR = "#cbd5e1"
PDF_TABLE_HEADER_BG = "#f1f5f9"
PDF_FOOTER_TEXT = "This is a computer-generated tax invoice and does not require a signature."
PDF_QUOTATION_TITLE = "QUOTATION"
PDF_CREDIT_NOTE_TITLE = "CREDIT NOTE"
PDF_QUOTATION_FOOTER = (
    "This is a computer-generated quotation and is not a tax invoice until converted."
)
PDF_CREDIT_NOTE_FOOTER = (
    "This is a computer-generated credit note issued against the referenced tax invoice."
)
BLOB_QUOTATION_PREFIX = "quotations"

# --- Collections / reminders -----------------------------------------------
class ReminderTrigger:
    MANUAL = "MANUAL"
    DUE_SOON = "DUE_SOON"
    DUE_TODAY = "DUE_TODAY"
    OVERDUE_7 = "OVERDUE_7"
    OVERDUE_15 = "OVERDUE_15"
    OVERDUE_30 = "OVERDUE_30"


REMINDER_SCHEDULE_DAYS_BEFORE_DUE = 3
REMINDER_OVERDUE_MILESTONES: tuple[int, ...] = (7, 15, 30)
SCHEDULED_REMINDER_JOB_HOUR = 9
SCHEDULED_REMINDER_JOB_MINUTE = 0
CALL_TODAY_LIMIT = 10

# --- UPI payments ----------------------------------------------------------
UPI_CURRENCY = "INR"
UPI_LINK_LABEL = "Scan QR or pay via UPI"
PDF_UPI_SECTION_TITLE = "Pay via UPI"

# --- Customer statements ---------------------------------------------------
BLOB_STATEMENT_PREFIX = "statements"
PDF_STATEMENT_TITLE = "Statement of Account"

# --- Background jobs -------------------------------------------------------
OVERDUE_JOB_INTERVAL_HOURS = 6

# --- WhatsApp webhook ------------------------------------------------------
WHATSAPP_WEBHOOK_PATH = f"{API_V1_PREFIX}/webhooks/whatsapp"
WHATSAPP_HUB_MODE = "subscribe"
WHATSAPP_SIGNATURE_HEADER = "X-Hub-Signature-256"
WHATSAPP_GRAPH_API_VERSION = "v21.0"
WHATSAPP_GRAPH_BASE_URL = "https://graph.facebook.com"
WHATSAPP_TEMPLATE_REMINDER_EN = "payment_reminder_en"
WHATSAPP_TEMPLATE_REMINDER_HI = "payment_reminder_hi"
WHATSAPP_TEMPLATE_INVOICE_SHARE = "invoice_share"
WHATSAPP_TEMPLATE_COMPLIANCE_REMINDER = "compliance_reminder"
WHATSAPP_REMINDER_BODY: dict[str, dict[str, str]] = {
    "due_soon": {
        "en": "Hi {customer_name}, invoice {invoice_number} for ₹{amount_due} is due in {days} days. Please pay on time.",
        "hi": "नमस्ते {customer_name}, आपका बिल {invoice_number} ₹{amount_due} {days} दिन में देय है। कृपया समय पर भुगतान करें।",
    },
    "due_today": {
        "en": "Hi {customer_name}, invoice {invoice_number} for ₹{amount_due} is due today. Please pay today.",
        "hi": "नमस्ते {customer_name}, आपका बिल {invoice_number} ₹{amount_due} आज देय है। कृपया भुगतान करें।",
    },
    "overdue": {
        "en": "Hi {customer_name}, invoice {invoice_number} has ₹{amount_due} due ({days_overdue} days overdue). Please pay at earliest.",
        "hi": "नमस्ते {customer_name}, आपका बिल {invoice_number} ₹{amount_due} बकाया है ({days_overdue} दिन)। कृपया भुगतान करें।",
    },
}
WHATSAPP_COPILOT_MAX_REPLY_CHARS = 4000
WHATSAPP_COPILOT_UNLINKED_REPLY = (
    "Hi! Link this WhatsApp number in KuberAIQ: Settings → Integrations → WhatsApp AI copilot. "
    "https://www.kuberaiq.com/settings"
)

# --- Reminder languages ----------------------------------------------------
REMINDER_LANGUAGES: tuple[str, ...] = ("en", "hi")
DEFAULT_REMINDER_LANGUAGE = "en"

# --- Entra OIDC ------------------------------------------------------------
ENTRA_AUTHORITY_BASE = "https://login.microsoftonline.com"
ENTRA_SCOPES: tuple[str, ...] = ("openid", "profile", "email", "offline_access")
