"""Structured JSON logging via structlog (no PII/secrets in logs)."""
from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import settings

_SENSITIVE_KEYS = {"authorization", "password", "token", "access_token", "secret", "api_key"}


def _redact(_: object, __: str, event_dict: dict) -> dict:
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***redacted***"
    return event_dict


def configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _redact,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "kuberaiq") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
