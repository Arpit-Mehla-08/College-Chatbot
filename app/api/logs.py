"""Query logs API endpoint."""

from fastapi import APIRouter, Query

from app.core.logger import query_logger

router = APIRouter()


@router.get("/logs")
async def get_logs(
    limit: int = Query(default=50, ge=1, le=200, description="Max entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
):
    """
    Get query logs with pagination.

    Returns logs in reverse chronological order (most recent first).
    """
    logs = query_logger.get_logs(limit=limit, offset=offset)
    total = query_logger.get_total_count()

    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
