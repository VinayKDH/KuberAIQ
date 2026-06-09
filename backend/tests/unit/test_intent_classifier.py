"""Intent classifier tests."""
from __future__ import annotations

from app.core.constants import AiRoute
from app.infrastructure.ai.intent_classifier import classify_route


def test_pending_money_routes_to_collections() -> None:
    result = classify_route("How much money is pending?")
    assert result["route"] == AiRoute.COLLECTIONS


def test_help_routes_to_help() -> None:
    result = classify_route("help")
    assert result["route"] == AiRoute.HELP


def test_revenue_routes_to_dashboard() -> None:
    result = classify_route("What is my revenue this month?")
    assert result["route"] == AiRoute.DASHBOARD
