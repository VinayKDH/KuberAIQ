"""Tests for PDF paragraph helpers."""
from __future__ import annotations

from reportlab.lib.styles import getSampleStyleSheet

from app.infrastructure.pdf.pdf_common import html_para, para


def test_para_escapes_html_tags() -> None:
    style = getSampleStyleSheet()["Normal"]
    paragraph = para("<b>Hello</b>", style)
    assert "&lt;b&gt;" in paragraph.text


def test_html_para_renders_markup() -> None:
    style = getSampleStyleSheet()["Normal"]
    paragraph = html_para("<b>Hello</b>", style)
    assert paragraph.text == "<b>Hello</b>"
