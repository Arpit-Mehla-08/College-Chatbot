"""Query logging for debugging and accuracy auditing."""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings


@dataclass
class QueryLogEntry:
    """A single query log entry."""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_question: str = ""
    classified_domain: Optional[str] = None
    generated_sql: Optional[str] = None
    validation_passed: Optional[bool] = None
    validation_error: Optional[str] = None
    execution_time_ms: Optional[float] = None
    row_count: Optional[int] = None
    is_clarification: bool = False
    error: Optional[str] = None
    conversation_id: Optional[str] = None


class QueryLogger:
    """
    Structured query logger.

    Stores logs as JSON lines in a file (configurable via QUERY_LOG_FILE).
    Thread-safe via append-only file writes.
    """

    def __init__(self, log_file: Optional[str] = None):
        self._log_file = log_file or settings.QUERY_LOG_FILE

    def log(self, entry: QueryLogEntry) -> None:
        """Append a log entry to the log file."""
        try:
            entry_dict = asdict(entry)
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry_dict, default=str) + "\n")
        except Exception:
            # Logging should never crash the app
            pass

    def get_logs(
        self, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """
        Read log entries with pagination.

        Args:
            limit: Max entries to return
            offset: Number of entries to skip (from the end)

        Returns:
            List of log entry dicts, most recent first.
        """
        if not os.path.exists(self._log_file):
            return []

        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Parse all lines (most recent last in file)
            entries = []
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Return most recent first
            entries.reverse()

            # Apply pagination
            return entries[offset : offset + limit]

        except Exception:
            return []

    def get_total_count(self) -> int:
        """Get total number of log entries."""
        if not os.path.exists(self._log_file):
            return 0
        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def clear(self) -> None:
        """Clear all logs (for testing)."""
        try:
            if os.path.exists(self._log_file):
                os.remove(self._log_file)
        except Exception:
            pass


# Singleton instance
query_logger = QueryLogger()
