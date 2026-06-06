"""HTTP middleware — request ID, logging, security headers."""
from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants import RATE_LIMIT_DEFAULT_PER_MIN

logger = structlog.get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        structlog.contextvars.unbind_contextvars("request_id")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter (per-IP, dev-grade)."""

    _counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.endswith("/health"):
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = self._counts.setdefault(ip, [])
        window[:] = [t for t in window if now - t < 60]
        if len(window) >= RATE_LIMIT_DEFAULT_PER_MIN:
            return Response(status_code=429, content='{"error":"rate limited"}', media_type="application/json")
        window.append(now)
        return await call_next(request)
