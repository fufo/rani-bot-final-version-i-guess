"""
╔══════════════════════════════════════════════════════════╗
║         TELEGRAM SHOP BOT - ERROR TRACKER                ║
║  Collects, deduplicates, and reports runtime errors      ║
╚══════════════════════════════════════════════════════════╝
"""

import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  IN-MEMORY ERROR STORE
# ─────────────────────────────────────────────

class ErrorTracker:
    """
    Tracks recent errors with deduplication, counts, and timestamps.
    Stored in-memory; survives the session but not restarts.
    """

    MAX_ERRORS = 200
    DEDUP_WINDOW = 300  # seconds — same error within 5 min = one entry

    def __init__(self):
        # error_key -> {count, first_seen, last_seen, sample_msg}
        self._errors: Dict[str, dict] = {}
        self._recent: List[dict] = []   # flat log for the admin panel

    def record(self, context: str, error: Exception, user_id: int = None) -> None:
        """Record an error occurrence."""
        key = f"{context}:{type(error).__name__}:{str(error)[:60]}"
        now = time.time()
        now_str = datetime.now().strftime("%d %b %H:%M:%S")

        if key in self._errors:
            entry = self._errors[key]
            entry["count"] += 1
            entry["last_seen"] = now_str
        else:
            self._errors[key] = {
                "context": context,
                "type":    type(error).__name__,
                "message": str(error)[:200],
                "count":   1,
                "first_seen": now_str,
                "last_seen":  now_str,
                "user_id": user_id,
            }

        # Flat log for timeline view
        self._recent.append({
            "ts":      now_str,
            "context": context,
            "type":    type(error).__name__,
            "msg":     str(error)[:120],
            "user_id": user_id,
        })
        if len(self._recent) > self.MAX_ERRORS:
            self._recent = self._recent[-self.MAX_ERRORS:]

    def get_summary(self, limit: int = 15) -> List[dict]:
        """Top errors by frequency."""
        sorted_errors = sorted(
            self._errors.values(),
            key=lambda x: x["count"],
            reverse=True
        )
        return sorted_errors[:limit]

    def get_recent(self, limit: int = 20) -> List[dict]:
        return list(reversed(self._recent[-limit:]))

    def clear(self) -> None:
        self._errors.clear()
        self._recent.clear()

    @property
    def total_unique(self) -> int:
        return len(self._errors)

    @property
    def total_occurrences(self) -> int:
        return sum(e["count"] for e in self._errors.values())


# Singleton
error_tracker = ErrorTracker()
