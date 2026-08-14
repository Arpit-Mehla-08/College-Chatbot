"""Database schema introspection module."""

from typing import Any

from app.core.config import settings
from app.db.connection import execute_read_query


async def get_table_names() -> list[str]:
    """Get all table names from the database."""
    if settings.USE_METABASE and settings.METABASE_URL:
        from app.db.metabase_client import metabase_client
        return await metabase_client.get_tables()

    if settings.is_sqlite:
        results = await execute_read_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row["name"] for row in results]
    else:
        results = await execute_read_query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
        return [row["table_name"] for row in results]


async def get_table_columns(table_name: str) -> list[dict[str, Any]]:
    """Get column info for a specific table."""
    if settings.USE_METABASE and settings.METABASE_URL:
        # Use Metabase's native query to get column info
        results = await execute_read_query(
            f"SELECT column_name, data_type, is_nullable, column_default "
            f"FROM information_schema.columns "
            f"WHERE table_schema = 'public' AND table_name = '{table_name}' "
            f"ORDER BY ordinal_position"
        )
        return [
            {
                "column_name": row["column_name"],
                "data_type": row["data_type"],
                "is_nullable": row.get("is_nullable", "YES") == "YES",
                "is_primary_key": False,
                "default_value": row.get("column_default"),
            }
            for row in results
        ]

    if settings.is_sqlite:
        results = await execute_read_query(f"PRAGMA table_info('{table_name}')")
        return [
            {
                "column_name": row["name"],
                "data_type": row["type"],
                "is_nullable": not row["notnull"],
                "is_primary_key": bool(row["pk"]),
                "default_value": row["dflt_value"],
            }
            for row in results
        ]
    else:
        results = await execute_read_query(
            f"SELECT column_name, data_type, is_nullable, column_default "
            f"FROM information_schema.columns "
            f"WHERE table_schema = 'public' AND table_name = '{table_name}' "
            f"ORDER BY ordinal_position"
        )
        return [
            {
                "column_name": row["column_name"],
                "data_type": row["data_type"],
                "is_nullable": row["is_nullable"] == "YES",
                "is_primary_key": False,  # Would need additional query for PK info
                "default_value": row.get("column_default"),
            }
            for row in results
        ]


async def get_full_schema() -> dict[str, list[dict[str, Any]]]:
    """Get complete schema: all tables with their columns."""
    # When using Metabase, skip live introspection (too slow - 74 API calls).
    # Use the annotations YAML as the source of truth instead.
    if settings.USE_METABASE and settings.METABASE_URL:
        return _get_schema_from_annotations()

    tables = await get_table_names()
    schema = {}
    for table in tables:
        schema[table] = await get_table_columns(table)
    return schema


def _get_schema_from_annotations() -> dict[str, list[dict[str, Any]]]:
    """Build schema dict from annotations YAML (no DB calls needed)."""
    import os
    import yaml

    annotations_path = os.path.join(
        os.path.dirname(__file__), "annotations.yaml"
    )
    with open(annotations_path, "r") as f:
        annotations = yaml.safe_load(f)

    schema = {}
    for table_name, table_info in annotations.get("tables", {}).items():
        columns = []
        for col_name, col_desc in table_info.get("columns", {}).items():
            columns.append({
                "column_name": col_name,
                "data_type": "text",  # Default type since we don't have it
                "is_nullable": True,
                "is_primary_key": col_name == "id",
                "default_value": None,
            })
        schema[table_name] = columns
    return schema
