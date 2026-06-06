"""Central registry of static values (per project convention: no magic literals).

Every fixed string, number, label, or enum-like value used across the codebase lives
here so behaviour is consistent and changes happen in one place.
"""
from __future__ import annotations

from decimal import Decimal

# --- App metadata ----------------------------------------------------------
APP_NAME = "VyaparAI"
APP_TAGLINE = "AI Business Manager for Indian MSMEs"
API_V1_PREFIX = "/api/v1"

# --- Currency / locale -----------------------------------------------------
CURRENCY_CODE = "INR"
CURRENCY_SYMBOL = "₹"
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
GST_TOLERANCE = Decimal("0.02")  # acceptable rounding delta when validating totals
GSTIN_LENGTH = 15
GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

# --- Phone -----------------------------------------------------------------
INDIA_PHONE_REGEX = r"^[6-9]\d{9}$"
INDIA_COUNTRY_CODE = "91"

# --- Invoice numbering -----------------------------------------------------
DEFAULT_INVOICE_PREFIX = "INV"
INVOICE_NUMBER_PAD = 4  # INV/2025-26/0042
FINANCIAL_YEAR_START_MONTH = 4  # April

# --- Defaults --------------------------------------------------------------
DEFAULT_DUE_DAYS = 15
DEFAULT_UNIT = "NOS"
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# --- Collections -----------------------------------------------------------
REMINDER_COOLDOWN_HOURS = 48

# --- Auth / security -------------------------------------------------------
ACCESS_TOKEN_TTL_MINUTES = 15
REFRESH_TOKEN_TTL_DAYS = 7
JWT_ALGORITHM = "HS256"  # RS256 in production with Key Vault keys
AUTH_SCHEME = "Bearer"

# --- Rate limits (requests per window) -------------------------------------
RATE_LIMIT_DEFAULT_PER_MIN = 300
RATE_LIMIT_IP_PER_MIN = 100
RATE_LIMIT_AUTH_PER_MIN = 10
RATE_LIMIT_AI_PER_MIN = 20

# --- AI --------------------------------------------------------------------
AI_MAX_MESSAGE_LEN = 2000
AI_HISTORY_TURNS = 10
AI_RESPONSE_MAX_LEN = 1000

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
    REMINDER_SENT = "REMINDER_SENT"
    AI_TOOL_CALL = "AI_TOOL_CALL"


# --- Entity type labels (for audit logs) -----------------------------------
class EntityType:
    INVOICE = "invoice"
    CUSTOMER = "customer"
    PAYMENT = "payment"
    REMINDER = "reminder"
    COMPANY = "company"
    USER = "user"


# --- Health ----------------------------------------------------------------
HEALTH_LIVE_PATH = "/health"
HEALTH_READY_PATH = "/health/ready"

# --- Demo seed (local mode) ------------------------------------------------
DEMO_COMPANY_NAME = "Demo Traders Pvt Ltd"
DEMO_COMPANY_GSTIN = "27AAPFU0939F1ZV"
DEMO_COMPANY_STATE = "27"
DEMO_COMPANY_ADDRESS = "MIDC, Pune, Maharashtra"
DEMO_USER_EMAIL = "owner@demo.vyaparai.com"
DEMO_USER_NAME = "Demo Owner"

# --- Aging buckets ---------------------------------------------------------
AGING_BUCKETS: tuple[str, ...] = ("0-30", "31-60", "61-90", "90+")

# --- AI routes / intents ---------------------------------------------------
class AiRoute:
    INVOICE = "invoice"
    COLLECTIONS = "collections"
    DASHBOARD = "dashboard"
    CUSTOMER = "customer"
    CLARIFY = "clarify"


class AiIntent:
    CREATE_INVOICE = "create_invoice"
    LIST_OVERDUE = "list_overdue"
    SEND_REMINDER = "send_reminder"
    GET_DASHBOARD = "get_dashboard"
    FIND_CUSTOMER = "find_customer"
    CREATE_CUSTOMER = "create_customer"
    CLARIFY = "clarify"


# --- PDF / storage ---------------------------------------------------------
PDF_SIGNED_URL_TTL_SECONDS = 3600
BLOB_INVOICE_PREFIX = "invoices"

# --- WhatsApp webhook ------------------------------------------------------
WHATSAPP_HUB_MODE = "subscribe"
WHATSAPP_SIGNATURE_HEADER = "X-Hub-Signature-256"
