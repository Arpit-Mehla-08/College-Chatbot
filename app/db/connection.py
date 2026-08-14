"""Database connection layer with SQLAlchemy async support."""

import os
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async SQLAlchemy engine."""
    global _engine
    if _engine is None:
        connect_args = {}
        if settings.is_sqlite:
            connect_args = {"check_same_thread": False}

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.is_development,
            connect_args=connect_args,
        )
    return _engine


async def reset_engine() -> None:
    """Reset the engine (useful for testing)."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def execute_read_query(sql: str) -> list[dict[str, Any]]:
    """
    Execute a read-only SQL query and return results as list of dicts.

    Routes through Metabase API if USE_METABASE=true, otherwise direct DB.

    Args:
        sql: The SQL SELECT query to execute.

    Returns:
        List of dictionaries, one per row, with column names as keys.

    Raises:
        RuntimeError: If query execution fails.
    """
    # Route through Metabase if configured
    if settings.USE_METABASE and settings.METABASE_URL:
        from app.db.metabase_client import metabase_client
        return await metabase_client.execute_query(sql)

    # Direct database execution
    engine = get_engine()

    try:
        async with engine.connect() as conn:
            # Set statement timeout for PostgreSQL
            if not settings.is_sqlite:
                timeout_ms = settings.QUERY_TIMEOUT_SECONDS * 1000
                await conn.execute(
                    text(f"SET statement_timeout = {timeout_ms}")
                )

            result = await conn.execute(text(sql))
            rows = result.fetchall()
            columns = list(result.keys())

            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        raise RuntimeError(f"Query execution failed: {str(e)}") from e


async def init_mock_db() -> None:
    """Initialize the mock SQLite database with schema and seed data."""
    import logging

    if not settings.is_sqlite:
        logging.info("Skipping mock DB init - not using SQLite")
        return

    # Skip mock DB init if using Metabase
    if settings.USE_METABASE:
        logging.info("Skipping mock DB init - USE_METABASE=true. Using real database via Metabase.")
        return

    logging.info("Initializing mock SQLite database with fresh schema and seed data...")
    engine = get_engine()

    # Read schema SQL
    schema_path = os.path.join(os.path.dirname(__file__), "mock_schema.sql")
    seed_path = os.path.join(os.path.dirname(__file__), "seed_data.sql")

    async with engine.begin() as conn:
        # Drop existing tables first to avoid UNIQUE constraint issues on re-init
        with open(schema_path, "r") as f:
            schema_sql = f.read()

        # Extract table names and drop them in reverse order
        import re
        table_names = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", schema_sql)
        for table in reversed(table_names):
            await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))

        # Create tables
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))

        # Seed data
        with open(seed_path, "r") as f:
            seed_sql = f.read()

        for statement in seed_sql.split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))
