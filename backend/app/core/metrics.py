"""Lightweight in-process request metrics (dev/staging; App Insights in prod)."""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class AppMetrics:
    requests_total: int = 0
    errors_total: int = 0
    ai_requests_total: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_request(self, *, path: str, status: int) -> None:
        with self._lock:
            self.requests_total += 1
            if status >= 500:
                self.errors_total += 1
            if "/ai/" in path:
                self.ai_requests_total += 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "requests_total": self.requests_total,
                "errors_total": self.errors_total,
                "ai_requests_total": self.ai_requests_total,
            }


metrics = AppMetrics()
