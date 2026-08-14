"""Week boundary utilities for trend/comparison queries."""

from datetime import date, timedelta

from app.core.config import settings


def get_week_boundaries(reference_date: date | None = None) -> dict:
    """
    Get week boundary dates based on the configured week definition.

    Args:
        reference_date: The reference date (defaults to today).

    Returns:
        Dict with 'current_week_start', 'current_week_end',
        'previous_week_start', 'previous_week_end'.
    """
    if reference_date is None:
        reference_date = date.today()

    if settings.WEEK_DEFINITION == "calendar":
        # Calendar week: Monday to Sunday
        # Find the Monday of the current week
        days_since_monday = reference_date.weekday()  # 0=Mon, 6=Sun
        current_week_start = reference_date - timedelta(days=days_since_monday)
        current_week_end = current_week_start + timedelta(days=6)

        # Previous week
        previous_week_start = current_week_start - timedelta(days=7)
        previous_week_end = current_week_start - timedelta(days=1)
    else:
        # Rolling 7 days
        current_week_end = reference_date
        current_week_start = reference_date - timedelta(days=6)

        previous_week_end = current_week_start - timedelta(days=1)
        previous_week_start = previous_week_end - timedelta(days=6)

    return {
        "current_week_start": current_week_start.isoformat(),
        "current_week_end": current_week_end.isoformat(),
        "previous_week_start": previous_week_start.isoformat(),
        "previous_week_end": previous_week_end.isoformat(),
    }


def get_week_context_for_prompt() -> str:
    """
    Get a human-readable week context string for LLM prompts.

    Returns a string describing the current and previous week date ranges.
    """
    boundaries = get_week_boundaries()
    return (
        f"Week definition: {settings.WEEK_DEFINITION}\n"
        f"Current week: {boundaries['current_week_start']} to {boundaries['current_week_end']}\n"
        f"Previous week: {boundaries['previous_week_start']} to {boundaries['previous_week_end']}\n"
        f"For the mock data, use these known weeks:\n"
        f"  Week 1: 2024-01-15 to 2024-01-19 (Mon-Fri)\n"
        f"  Week 2: 2024-01-22 to 2024-01-26 (Mon-Fri)"
    )
