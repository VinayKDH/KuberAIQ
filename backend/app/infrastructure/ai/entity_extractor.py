"""Rule-based entity extraction for AI copilot — reliable fallback and Azure enricher."""
from __future__ import annotations

import re
from typing import Any

from app.core.constants import (
    AI_CUSTOMER_NAME_STOP_WORDS,
    AI_INVOICE_LINE_ITEM_PATTERN,
    AI_INVOICE_UNIT_ALIASES,
    AiRoute,
)

_PHONE_RE = re.compile(r"\b(\d{10})\b")
_PRICE_RE = re.compile(
    r"(?:at|@|₹|rs\.?|rate)\s*(\d+(?:\.\d+)?)",
    re.I,
)
_GST_RE = re.compile(r"(\d+(?:\.\d+)?)%\s*gst", re.I)
_TRAILING_CUSTOMER_RE = re.compile(
    r"\bfor\s+([A-Za-z][A-Za-z0-9\s.&'-]{1,60}?)\s*$",
    re.I,
)
_INVOICE_TO_CUSTOMER_RE = re.compile(
    r"\b(?:invoice|bill)\s+(?:to|for)\s+([A-Za-z][A-Za-z0-9\s.&'-]{2,}?)"
    r"(?:\s+for\s+\d|\s+with\s+|\s+of\s+\d|\s+at\s|@|\s+\d+\s*(?:kg|bags?|litre)|$)",
    re.I,
)
_INVOICE_DIRECT_CUSTOMER_RE = re.compile(
    r"\b(?:invoice|bill)\s+(?:for\s+)?([A-Za-z][A-Za-z0-9\s.&'-]{2,}?)"
    r"(?:\s+for\s+\d|\s+with\s+|\s+of\s+\d|\s+at\s|@|\s+\d+\s*(?:kg|bags?|litre)|$)",
    re.I,
)
_CUSTOMER_CREATE_RE = re.compile(
    r"(?:create|add|new)\s+customer\s+(.+)$",
    re.I,
)
_LINE_ITEM_ANYWHERE_RE = re.compile(
    r"(?:\bfor\s+)?(\d+(?:\.\d+)?)\s*"
    r"(bags?|kg|kgs?|nos|units?|pcs?|pieces?|liters?|litres?|ltr|litre)"
    r"(?:\s+(?:of\s+)?([A-Za-z][A-Za-z\s]+?))?"
    r"(?=\s+and\s+|\s+at\s|@|\s+for\s+[A-Za-z]|\s*$)",
    re.I,
)
_CUSTOMER_FIND_RE = re.compile(
    r"(?:find|search|lookup|show)\s+customer\s+(.+)$",
    re.I,
)
_INVOICE_PREAMBLE_RE = re.compile(
    r"^(?:please\s+)?(?:create|make|generate|raise|new)?\s*"
    r"(?:the\s+)?(?:an?\s+)?(?:invoice|bill)\s+(?:of\s+)?",
    re.I,
)


def _normalize_unit(raw: str | None) -> str:
    if not raw:
        return "NOS"
    key = raw.lower().rstrip("s") if raw.lower() in {"bags", "kgs", "pcs", "units", "litres"} else raw.lower()
    return AI_INVOICE_UNIT_ALIASES.get(key, raw.upper())


def _clean_customer_name(name: str | None) -> str | None:
    if not name:
        return None
    cleaned = name.strip().strip(".,;:")
    if not cleaned:
        return None
    lower = cleaned.lower()
    if lower in AI_CUSTOMER_NAME_STOP_WORDS:
        return None
    if len(cleaned) < 2:
        return None
    return cleaned


def _extract_invoice_customer(message: str) -> str | None:
    """Prefer trailing 'for CUSTOMER' — avoids mistaking 'invoice of 50 bags' as a name."""
    trailing = _TRAILING_CUSTOMER_RE.search(message)
    if trailing:
        candidate = _clean_customer_name(trailing.group(1).strip())
        if candidate and not re.search(r"\bfor\s+\d", candidate):
            phone = extract_phone_from_text(candidate)
            if phone:
                candidate = re.sub(rf"\b{re.escape(phone)}\b", "", candidate).strip()
                candidate = _clean_customer_name(candidate)
            if candidate:
                return candidate

    direct = _INVOICE_DIRECT_CUSTOMER_RE.search(message)
    if direct:
        candidate = _clean_customer_name(direct.group(1).strip())
        if candidate:
            phone = extract_phone_from_text(candidate)
            if phone:
                candidate = re.sub(rf"\b{re.escape(phone)}\b", "", candidate).strip()
                candidate = _clean_customer_name(candidate)
            if candidate:
                return candidate

    billed = _INVOICE_TO_CUSTOMER_RE.search(message)
    if billed:
        candidate = _clean_customer_name(billed.group(1).strip())
        if candidate:
            phone = extract_phone_from_text(candidate)
            if phone:
                candidate = re.sub(rf"\b{re.escape(phone)}\b", "", candidate).strip()
                candidate = _clean_customer_name(candidate)
            if candidate:
                return candidate

    return None


def _strip_customer_suffix(text: str) -> str:
    """Remove trailing 'for CUSTOMER' before parsing line items."""
    return _TRAILING_CUSTOMER_RE.sub("", text).strip()


def _looks_like_line_item(fragment: str) -> bool:
    return bool(AI_INVOICE_LINE_ITEM_PATTERN.match(fragment.strip()))


def _split_line_item_clauses(text: str) -> list[str]:
    """Split '50 bags cement and 2 litre sealant' on ' and ' when both sides are items."""
    parts: list[str] = []
    buffer = text
    while " and " in buffer.lower():
        idx = buffer.lower().find(" and ")
        left = buffer[:idx].strip()
        right = buffer[idx + 5 :].strip()
        if _looks_like_line_item(left) and _looks_like_line_item(right):
            parts.append(left)
            buffer = right
        else:
            break
    if buffer.strip():
        parts.append(buffer.strip())
    return parts


def _parse_line_item_clause(clause: str) -> dict[str, Any] | None:
    match = AI_INVOICE_LINE_ITEM_PATTERN.match(clause.strip())
    if not match:
        return None
    qty = float(match.group(1))
    unit = _normalize_unit(match.group(2))
    description = (match.group(3) or "Item").strip().title()
    if description.lower() in AI_CUSTOMER_NAME_STOP_WORDS:
        return None
    return {
        "quantity": qty,
        "unit": unit,
        "description": description,
        "unit_price": None,
    }


def _extract_line_items(message: str, customer_name: str | None) -> list[dict[str, Any]]:
    working = message
    working = _INVOICE_PREAMBLE_RE.sub("", working).strip()
    working = _strip_customer_suffix(working)

    items: list[dict[str, Any]] = []
    for clause in _split_line_item_clauses(working):
        parsed = _parse_line_item_clause(clause)
        if parsed:
            items.append(parsed)

    if not items:
        for match in _LINE_ITEM_ANYWHERE_RE.finditer(message):
            description = (match.group(3) or "Item").strip().title()
            if description.lower() in AI_CUSTOMER_NAME_STOP_WORDS:
                description = "Item"
            items.append(
                {
                    "quantity": float(match.group(1)),
                    "unit": _normalize_unit(match.group(2)),
                    "description": description,
                    "unit_price": None,
                }
            )

    if not items:
        for keyword, label in (
                ("cement", "OPC 53 Grade Cement"),
                ("roof sealant", "Roof Sealant"),
                ("paneer", "Paneer"),
                ("khoya", "Khoya"),
        ):
            if re.search(rf"\b{re.escape(keyword)}\b", message, re.I):
                items.append(
                    {
                        "quantity": 1.0,
                        "unit": "NOS",
                        "description": label,
                        "unit_price": None,
                    }
                )
                break

    global_price = _PRICE_RE.search(message)
    if global_price and items:
        price = float(global_price.group(1))
        for item in items:
            if item.get("unit_price") is None:
                item["unit_price"] = price

    return items


def extract_phone_from_text(text: str) -> str | None:
    """Return the first 10-digit mobile in text, skipping price-like numbers."""
    for match in _PHONE_RE.finditer(text):
        phone = match.group(1)
        prefix = text[max(0, match.start() - 6) : match.start()].lower()
        if any(token in prefix for token in ("at ", "@", "rs", "rate ", "₹")):
            continue
        return phone
    return None


def extract_invoice_entities(message: str) -> dict[str, Any]:
    customer_name = _extract_invoice_customer(message)
    customer_phone = extract_phone_from_text(message)
    if customer_name and customer_phone:
        customer_name = re.sub(rf"\b{re.escape(customer_phone)}\b", "", customer_name).strip()
        customer_name = _clean_customer_name(customer_name)
    line_items = _extract_line_items(message, customer_name)
    gst_match = _GST_RE.search(message)

    first = line_items[0] if line_items else {}
    return {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "line_items": line_items,
        "quantity": first.get("quantity"),
        "unit": first.get("unit", "NOS"),
        "description": first.get("description", "Item"),
        "unit_price": first.get("unit_price"),
        "gst_rate": float(gst_match.group(1)) if gst_match else None,
    }


def _parse_labeled_customer_details(message: str) -> dict[str, str | None]:
    """Parse 'Name Kamal Joshi. Phone 9258843443' and similar follow-ups."""
    name: str | None = None
    phone: str | None = None

    name_match = re.search(
        r"\bname\s*[:\.\-]?\s*([A-Za-z][A-Za-z\s.'-]{1,60}?)"
        r"(?=\s*[,.\s]+(?:phone|mobile|number|\d{10})|\s*$)",
        message,
        re.I,
    )
    if name_match:
        name = _clean_customer_name(name_match.group(1).strip().rstrip(".,;:"))

    phone_match = re.search(
        r"\b(?:phone|mobile|number|contact)\s*[:\.\-]?\s*(\d{10})\b",
        message,
        re.I,
    )
    if phone_match:
        phone = phone_match.group(1)
    elif not phone:
        phone = extract_phone_from_text(message)

    return {"name": name, "phone": phone}


def _is_invoice_message(message: str) -> bool:
    lower = message.lower()
    return bool(
        re.search(r"\b(invoice|bill)\b", lower)
        and re.search(r"\b(create|make|raise|generate|new)\b", lower)
    ) or lower.startswith(("invoice ", "bill "))


def parse_customer_details_from_text(message: str) -> dict[str, str | None]:
    """Public helper for labeled or free-form customer name + phone parsing."""
    labeled = _parse_labeled_customer_details(message)
    if labeled.get("name") and labeled.get("phone"):
        return labeled

    create_match = _CUSTOMER_CREATE_RE.search(message)
    if create_match:
        name, phone = _parse_customer_name_phone(create_match.group(1))
        return {"name": name, "phone": phone}

    if _is_invoice_message(message):
        return {"name": None, "phone": extract_phone_from_text(message)}

    phone = extract_phone_from_text(message)
    name = labeled.get("name")
    if phone and not name:
        remainder = re.sub(rf"\b{re.escape(phone)}\b", "", message)
        remainder = re.sub(
            r"\b(?:name|phone|mobile|number|contact)\s*[:\.\-]?\s*",
            "",
            remainder,
            flags=re.I,
        ).strip(" .,;:-")
        name = _clean_customer_name(remainder) if remainder else None

    return {"name": name, "phone": phone}


def _parse_customer_name_phone(remainder: str) -> tuple[str | None, str | None]:
    """Parse 'Raj Traders 9876543210', 'for 9000000000', or '9876543210'."""
    text = remainder.strip()
    if not text:
        return None, None

    text = re.sub(r"^for\s+", "", text, flags=re.I).strip()
    phone_match = _PHONE_RE.search(text)
    phone = phone_match.group(1) if phone_match else None

    name_part = _PHONE_RE.sub("", text).strip()
    name_part = re.sub(r"^for\s+", "", name_part, flags=re.I).strip()
    name = _clean_customer_name(name_part) if name_part else None

    if phone and not name:
        if re.fullmatch(r"\d{10}", text.replace(" ", "")):
            return None, phone
        return None, phone

    if name and not phone and re.fullmatch(r"\d{10}", name.replace(" ", "")):
        return None, name

    return name, phone


def extract_customer_entities(message: str) -> dict[str, Any]:
    details = parse_customer_details_from_text(message)
    if details.get("name") and details.get("phone"):
        return {"name": details["name"], "phone": details["phone"]}

    create_match = _CUSTOMER_CREATE_RE.search(message)
    find_match = _CUSTOMER_FIND_RE.search(message)

    if create_match:
        name, phone = _parse_customer_name_phone(create_match.group(1))
    elif find_match:
        name, phone = _parse_customer_name_phone(find_match.group(1))
        if name and not phone:
            phone = None
    else:
        name = details.get("name")
        phone = details.get("phone")

    return {"name": name, "phone": phone}


def merge_extracted_entities(
    llm_entities: dict[str, Any],
    message: str,
    intent: str,
) -> dict[str, Any]:
    """Enrich or replace weak LLM extraction with deterministic rules."""
    if intent in {AiRoute.INVOICE, "invoice"}:
        rules = extract_invoice_entities(message)
        merged = dict(llm_entities)
        llm_customer = _clean_customer_name(merged.get("customer_name"))
        if not llm_customer or llm_customer.lower() in AI_CUSTOMER_NAME_STOP_WORDS:
            merged["customer_name"] = rules.get("customer_name")
        else:
            merged["customer_name"] = llm_customer

        llm_items = merged.get("line_items") or []
        if not llm_items and rules.get("line_items"):
            merged["line_items"] = rules["line_items"]
            first = rules["line_items"][0]
            merged.setdefault("quantity", first.get("quantity"))
            merged.setdefault("unit", first.get("unit"))
            merged.setdefault("description", first.get("description"))
            merged.setdefault("unit_price", first.get("unit_price"))
        elif not merged.get("description") or merged.get("description") == "Item":
            merged["description"] = rules.get("description", "Item")
            merged.setdefault("quantity", rules.get("quantity"))
            merged.setdefault("unit", rules.get("unit"))
        merged.setdefault("gst_rate", rules.get("gst_rate"))
        return merged

    if intent in {AiRoute.CUSTOMER, "customer"}:
        rules = extract_customer_entities(message)
        merged = dict(llm_entities)
        llm_name = _clean_customer_name(merged.get("name"))
        if not llm_name or llm_name.lower() in AI_CUSTOMER_NAME_STOP_WORDS:
            merged["name"] = rules.get("name")
        if not merged.get("phone"):
            merged["phone"] = rules.get("phone")
        return merged

    return llm_entities
