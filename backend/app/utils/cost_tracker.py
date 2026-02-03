"""Cost and usage tracking utility."""

from datetime import date, datetime
from typing import Any

from ..config import get_settings, Settings


class CostTracker:
    """Track API usage and enforce cost limits."""

    def __init__(self, settings: Settings | None = None):
        """Initialize cost tracker."""
        self.settings = settings or get_settings()
        self._daily_usage: dict[str, dict[str, Any]] = {}

    def _get_today_key(self) -> str:
        """Get today's date as string key."""
        return date.today().isoformat()

    def _get_today_usage(self) -> dict[str, Any]:
        """Get or create today's usage record."""
        today = self._get_today_key()
        if today not in self._daily_usage:
            self._daily_usage[today] = {
                "queries": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "started_at": datetime.utcnow().isoformat(),
            }
        return self._daily_usage[today]

    def can_process_query(self) -> tuple[bool, str]:
        """
        Check if a new query can be processed.

        Returns:
            Tuple of (allowed, reason)
        """
        usage = self._get_today_usage()

        if usage["queries"] >= self.settings.max_daily_queries:
            return False, f"Daily query limit ({self.settings.max_daily_queries}) reached. Try again tomorrow."

        if usage["cost_usd"] >= self.settings.max_daily_cost_usd:
            return False, f"Daily cost limit (${self.settings.max_daily_cost_usd:.2f}) reached. Try again tomorrow."

        return True, "OK"

    def track_query(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> dict[str, Any]:
        """
        Track a completed query.

        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            cost_usd: Estimated cost in USD

        Returns:
            Updated daily usage stats
        """
        usage = self._get_today_usage()
        usage["queries"] += 1
        usage["input_tokens"] += input_tokens
        usage["output_tokens"] += output_tokens
        usage["cost_usd"] += cost_usd
        return usage

    def get_usage_stats(self) -> dict[str, Any]:
        """Get current usage statistics."""
        usage = self._get_today_usage()
        return {
            "period": self._get_today_key(),
            "queries_today": usage["queries"],
            "total_tokens_used": usage["input_tokens"] + usage["output_tokens"],
            "total_cost_usd": usage["cost_usd"],
            "limits": {
                "max_queries": self.settings.max_daily_queries,
                "max_cost_usd": self.settings.max_daily_cost_usd,
            },
        }

    def reset_daily_usage(self) -> None:
        """Reset today's usage (for testing)."""
        today = self._get_today_key()
        if today in self._daily_usage:
            del self._daily_usage[today]


# Singleton instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get or create cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
