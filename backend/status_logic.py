"""Classify and stabilize one table using monotonic time in seconds."""
from dataclasses import dataclass
from typing import Literal

Status = Literal["unknown", "free", "partly_taken", "full", "items_only"]
CONFIRM_SECONDS = 2.0
MAX_CONFIRMATION_GAP = 4.0
STALE_SECONDS = 12.0


def classify(seats: int, people: int, items: int) -> Status:
    if people >= seats:
        return "full"
    if people > 0:
        return "partly_taken"
    return "items_only" if items else "free"


@dataclass
class TableState:
    status: Status = "unknown"
    candidate: Status = "unknown"
    candidate_since: float = 0
    items_since: float | None = None
    observed_at: float | None = None
    seats: int = 0
    people: int = 0
    items: int = 0

    def observe(self, seats: int, people: int, items: int, now: float) -> None:
        candidate = classify(seats, people, items)
        previous = self.observed_at
        if previous is None or now - previous >= STALE_SECONDS or seats != self.seats:
            self.status = self.candidate = "unknown"
            self.items_since = None
        elif now - previous > MAX_CONFIRMATION_GAP:
            self.candidate = self.status
        self.seats, self.people, self.items = seats, people, items
        self.observed_at = now
        if candidate != self.candidate:
            self.candidate, self.candidate_since = candidate, now
        elif candidate != self.status and now - self.candidate_since >= CONFIRM_SECONDS:
            self.status = candidate
            self.items_since = self.candidate_since if candidate == "items_only" else None

    def snapshot(self, table_id: int, now: float) -> dict:
        fresh = self.observed_at is not None and now - self.observed_at < STALE_SECONDS
        return {
            "table_id": table_id,
            "seats": self.seats,
            "people": self.people if fresh else None,
            "items": self.items if fresh else None,
            "status": self.status if fresh else "unknown",
            "items_seconds": int(now - self.items_since) if fresh and self.items_since is not None else 0,
            "pending_status": self.candidate if fresh and self.candidate != self.status else None,
        }
