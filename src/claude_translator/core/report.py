"""Aggregated sync reporting."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class SyncReport:
    """Aggregate counts for a sync run."""

    total: int = 0
    override: int = 0
    cache: int = 0
    llm: int = 0
    empty: int = 0
    skip: int = 0
    failed: int = 0

    def bump(self, status: str) -> SyncReport:
        allowed = {"override", "cache", "llm", "empty", "skip", "failed"}
        field = status if status in allowed else "skip"
        return replace(self, total=self.total + 1, **{field: getattr(self, field) + 1})

    def summary_line(self) -> str:
        parts = [f"total={self.total}"]
        for field in ("override", "cache", "llm", "empty", "skip", "failed"):
            value = getattr(self, field)
            if value:
                parts.append(f"{field}={value}")
        return "Sync complete: " + ", ".join(parts)

    @property
    def has_failures(self) -> bool:
        return self.failed > 0
