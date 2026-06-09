"""Shared PDF layout helpers."""
from __future__ import annotations

import re

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

_INDIAN_STATES: dict[str, str] = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
}


def state_label(code: str | None) -> str:
    if not code:
        return "—"
    return _INDIAN_STATES.get(code.zfill(2) if len(code) < 2 else code[:2], code)


def escape_xml(text: str) -> str:
    """Escape user-supplied text embedded in ReportLab markup."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def para(text: str, style: ParagraphStyle) -> Paragraph:
    safe = escape_xml(text or "—")
    return Paragraph(safe.replace("\n", "<br/>"), style)


def html_para(text: str, style: ParagraphStyle) -> Paragraph:
    """ReportLab Paragraph that renders intentional markup (<b>, <br/>, <font>, etc.)."""
    safe = re.sub(r"&(?!amp;|lt;|gt;|#)", "&amp;", text or "—")
    return Paragraph(safe.replace("\n", "<br/>"), style)
