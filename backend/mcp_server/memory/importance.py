"""Importance scoring strategy for memory promotion."""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ImportanceStrategy:
    """Importance scoring strategy — determines whether memory is worth keeping."""

    @staticmethod
    def from_user_saved() -> float:
        """User actively saved → high importance (0.8-1.0)."""
        return 0.9

    @staticmethod
    def from_auto_extracted(mentions: int = 1, recency_days: float = 0) -> float:
        """
        Auto-extracted → based on mention count and recency.

        Formula: min(0.3 + mentions * 0.1 - recency_days * 0.01, 0.8)
        """
        return min(0.3 + mentions * 0.1 - recency_days * 0.01, 0.8)

    @staticmethod
    def from_feedback_derived(rating: str) -> float:
        """User feedback derived → positive 0.7, negative 0.2."""
        return 0.7 if rating == "up" else 0.2

    @staticmethod
    def should_cleanup(importance: float, updated_at: datetime, max_days: int = 30) -> bool:
        """Low-importance memories older than max_days should be cleaned up."""
        return importance < 0.2 and (datetime.utcnow() - updated_at) > timedelta(days=max_days)

    @staticmethod
    def filter_by_importance(memories: list[dict], min_importance: float = 0.0) -> list[dict]:
        """Filter memories by minimum importance threshold."""
        return [m for m in memories if m.get("importance", 0) >= min_importance]

    @staticmethod
    def auto_promote_threshold() -> float:
        """Automatic promotion threshold — memories above this should be stored permanently."""
        return 0.5
