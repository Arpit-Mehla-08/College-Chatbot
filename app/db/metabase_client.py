"""Metabase API client for executing SQL queries."""

import httpx
from typing import Any, Optional

from app.core.config import settings


class MetabaseClient:
    """Executes SQL queries via Metabase's API."""

    def __init__(self):
        self.base_url = (settings.METABASE_URL or "").rstrip("/")
        self.database_id = settings.METABASE_DATABASE_ID
        self._session_token: Optional[str] = None

    async def _get_session_token(self) -> str:
        """Login to Metabase and get a session token."""
        if self._session_token:
            return self._session_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/session",
                json={
                    "username": settings.METABASE_USERNAME,
                    "password": settings.METABASE_PASSWORD,
                },
            )
            response.raise_for_status()
            self._session_token = response.json()["id"]
            return self._session_token

    async def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute a SQL query via Metabase API.

        Args:
            sql: The SQL SELECT query to execute.

        Returns:
            List of dicts (one per row).

        Raises:
            RuntimeError: If the query fails.
        """
        token = await self._get_session_token()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/dataset",
                    headers={"X-Metabase-Session": token},
                    json={
                        "database": self.database_id,
                        "type": "native",
                        "native": {"query": sql},
                    },
                )

                # If session expired, retry with fresh token
                if response.status_code == 401:
                    self._session_token = None
                    token = await self._get_session_token()
                    response = await client.post(
                        f"{self.base_url}/api/dataset",
                        headers={"X-Metabase-Session": token},
                        json={
                            "database": self.database_id,
                            "type": "native",
                            "native": {"query": sql},
                        },
                    )

                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Metabase query failed: {e.response.status_code} - {e.response.text}") from e
        except httpx.ConnectError as e:
            raise RuntimeError(f"Cannot connect to Metabase at {self.base_url}: {e}") from e

        # Parse Metabase response format into list of dicts
        if "data" not in data:
            error = data.get("error", "Unknown error")
            raise RuntimeError(f"Metabase query error: {error}")

        columns = [col["name"] for col in data["data"]["cols"]]
        rows = data["data"]["rows"]

        return [dict(zip(columns, row)) for row in rows]

    async def get_tables(self) -> list[str]:
        """Get list of tables from Metabase database metadata."""
        token = await self._get_session_token()

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/api/database/{self.database_id}/metadata",
                headers={"X-Metabase-Session": token},
            )
            response.raise_for_status()
            data = response.json()

        tables = []
        for table in data.get("tables", []):
            if table.get("visibility_type") is None:  # Skip hidden tables
                tables.append(table["name"])
        return sorted(tables)


# Singleton
metabase_client = MetabaseClient()
