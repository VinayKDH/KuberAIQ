"""Unit tests for AI entity extraction."""
from __future__ import annotations

import pytest

from app.infrastructure.ai.entity_extractor import (
    extract_customer_entities,
    extract_invoice_entities,
    extract_phone_from_text,
    merge_extracted_entities,
)


class TestExtractInvoiceEntities:
    def test_multi_item_invoice_with_trailing_customer(self) -> None:
        message = (
            "Create the invoice of 50 bags of cement and 2 litre of roof sealant "
            "for AIMLGYAN"
        )
        entities = extract_invoice_entities(message)
        assert entities["customer_name"] == "AIMLGYAN"
        assert len(entities["line_items"]) == 2
        assert entities["line_items"][0]["quantity"] == 50
        assert entities["line_items"][0]["unit"] == "BAG"
        assert "cement" in entities["line_items"][0]["description"].lower()
        assert entities["line_items"][1]["quantity"] == 2
        assert entities["line_items"][1]["unit"] == "LTR"
        assert "sealant" in entities["line_items"][1]["description"].lower()

    def test_simple_invoice_for_customer(self) -> None:
        message = "Create the invoice for AIMLGYAN"
        entities = extract_invoice_entities(message)
        assert entities["customer_name"] == "AIMLGYAN"

    def test_invoice_with_qty_and_price(self) -> None:
        message = "Invoice AI Confirm Co for 5 bags at 400"
        entities = extract_invoice_entities(message)
        assert entities["customer_name"] == "AI Confirm Co"
        assert entities["line_items"][0]["quantity"] == 5
        assert entities["line_items"][0]["unit_price"] == 400
        assert entities["line_items"][0]["description"] == "Bag"

    def test_invoice_customer_name_with_inline_phone(self) -> None:
        message = "Invoice New Person 9123456789 for 10 kg paneer at 200"
        entities = extract_invoice_entities(message)
        assert entities["customer_name"] == "New Person"
        assert entities["customer_phone"] == "9123456789"
        assert entities["line_items"][0]["description"] == "Paneer"
        assert entities["line_items"][0]["quantity"] == 10
        assert entities["line_items"][0]["unit_price"] == 200

    def test_phone_in_traders_name_not_treated_as_price(self) -> None:
        message = "Invoice Fresh Traders 9123456780 for 10 kg paneer at 200"
        entities = extract_invoice_entities(message)
        assert entities["customer_name"] == "Fresh Traders"
        assert entities["customer_phone"] == "9123456780"
        assert entities["line_items"][0]["unit_price"] == 200

    def test_does_not_use_of_as_customer(self) -> None:
        message = "Create the invoice of 50 bags of cement for Raj Traders"
        entities = extract_invoice_entities(message)
        assert entities["customer_name"] == "Raj Traders"
        assert entities["customer_name"] != "of"

    def test_gst_rate_extraction(self) -> None:
        message = "Invoice Raj for 10 kg paneer at 200 with 5% GST"
        entities = extract_invoice_entities(message)
        assert entities["gst_rate"] == 5


class TestExtractCustomerEntities:
    def test_phone_not_skipped_in_person_name(self) -> None:
        assert extract_phone_from_text("Invoice New Person 9123456789 for 10 kg") == "9123456789"

    def test_phone_skipped_after_at_price(self) -> None:
        assert extract_phone_from_text("Invoice Raj for 5 bags at 400") is None

    def test_phone_only_after_for(self) -> None:
        entities = extract_customer_entities("Add customer for 9000000000")
        assert entities["phone"] == "9000000000"
        assert entities["name"] is None

    def test_name_and_phone(self) -> None:
        entities = extract_customer_entities("Add customer Sprint Four Co 9123456780")
        assert entities["name"] == "Sprint Four Co"
        assert entities["phone"] == "9123456780"

    def test_find_customer(self) -> None:
        entities = extract_customer_entities("find customer AIMLGYAN")
        assert entities["name"] == "AIMLGYAN"

    def test_labeled_name_phone_follow_up(self) -> None:
        entities = extract_customer_entities("Name Kamal Joshi. Phone 9258843443")
        assert entities["name"] == "Kamal Joshi"
        assert entities["phone"] == "9258843443"

    def test_create_customer_name_only(self) -> None:
        entities = extract_customer_entities("create customer kamal joshi")
        assert entities["name"] == "kamal joshi"
        assert entities["phone"] is None


class TestMergeExtractedEntities:
    def test_replaces_stopword_customer_from_llm(self) -> None:
        llm = {
            "customer_name": "of",
            "line_items": [],
            "description": "Item",
        }
        message = (
            "Create the invoice of 50 bags of cement and 2 litre of roof sealant "
            "for AIMLGYAN"
        )
        merged = merge_extracted_entities(llm, message, "invoice")
        assert merged["customer_name"] == "AIMLGYAN"
        assert len(merged["line_items"]) == 2

    def test_replaces_stopword_customer_name_on_create(self) -> None:
        merged = merge_extracted_entities(
            {"name": "for", "phone": "9000000000"},
            "Add customer for 9000000000",
            "customer",
        )
        assert merged["name"] is None
        assert merged["phone"] == "9000000000"
