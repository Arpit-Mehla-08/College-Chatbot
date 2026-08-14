# Connecting to Real Database

This guide covers two ways to connect the chatbot to your real college PostgreSQL database:

1. **Direct PostgreSQL connection** (recommended for production)
2. **Via Metabase API** (if you only have Metabase access and no direct DB credentials)

---

## Option 1: Direct PostgreSQL Connection

This is the simplest and fastest approach. You just need the PostgreSQL connection string.

### What You Need

From your database admin or hosting provider, get:
- **Host**: e.g., `db.example.com` or `192.168.1.100`
- **Port**: usually `5432`
- **Database name**: e.g., `college_db`
- **Username**: e.g., `chatbot_reader`
- **Password**: the password for that user

### Step 1: Update .env

```env
# Replace the SQLite line with your PostgreSQL connection:
DATABASE_URL=postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME

# Example:
DATABASE_URL=postgresql+asyncpg://chatbot_reader:mypassword123@db.college.com:5432/college_production
```

### Step 2: Install asyncpg (if not already)

```bash
# With uv:
uv add asyncpg

# With pip:
pip install asyncpg
```

### Step 3: Create a Read-Only User (Recommended)

Ask your DBA to create a restricted user that can ONLY read data:

```sql
-- Run this on your PostgreSQL server as admin:

-- Create a read-only role
CREATE ROLE chatbot_reader WITH LOGIN PASSWORD 'strong_password_here';

-- Grant connect
GRANT CONNECT ON DATABASE college_db TO chatbot_reader;

-- Grant read access to all existing tables
GRANT USAGE ON SCHEMA public TO chatbot_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatbot_reader;

-- Grant read access to future tables too
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO chatbot_reader;
```

This ensures the chatbot can NEVER modify data, even if the SQL validator has a bug.

### Step 4: Update Schema Annotations

Edit `app/schema/annotations.yaml` to match your real table names:

```yaml
domains:
  attendance:
    tables:
      - your_actual_attendance_table_name
      - your_actual_student_table_name
    notes:
      - "Important: Use column_x for attendance status, not column_y"
```

The schema introspector will auto-detect your tables, but the annotations help the LLM understand what each table/column means.

### Step 5: Test the Connection

```bash
# Quick test
uv run python -c "
import asyncio
from app.db.connection import execute_read_query, reset_engine
from app.core.config import settings

async def test():
    await reset_engine()
    print(f'Connecting to: {settings.DATABASE_URL[:30]}...')
    result = await execute_read_query('SELECT COUNT(*) as count FROM information_schema.tables')
    print(f'Tables found: {result[0][\"count\"]}')

asyncio.run(test())
"
```

### Step 6: Discover Your Schema

Once connected, introspect what tables exist:

```bash
uv run python -c "
import asyncio
from app.db.connection import reset_engine
from app.schema.introspector import get_table_names, get_table_columns

async def discover():
    await reset_engine()
    tables = await get_table_names()
    print(f'Found {len(tables)} tables:')
    for t in sorted(tables):
        cols = await get_table_columns(t)
        col_names = [c['column_name'] for c in cols]
        print(f'  {t}: {col_names[:5]}...')  # First 5 columns

asyncio.run(discover())
"
```

Use this output to update your `annotations.yaml` with real table/column descriptions.

### Connection String Formats

| Scenario | Connection String |
|----------|------------------|
| Local PostgreSQL | `postgresql+asyncpg://user:pass@localhost:5432/dbname` |
| Remote server | `postgresql+asyncpg://user:pass@db.example.com:5432/dbname` |
| AWS RDS | `postgresql+asyncpg://user:pass@mydb.abc123.us-east-1.rds.amazonaws.com:5432/dbname` |
| Supabase | `postgresql+asyncpg://postgres:pass@db.xxxxx.supabase.co:5432/postgres` |
| With SSL | `postgresql+asyncpg://user:pass@host:5432/dbname?ssl=require` |

### Troubleshooting

| Error | Fix |
|-------|-----|
| `Connection refused` | Check host/port, ensure PostgreSQL is accepting connections |
| `Authentication failed` | Verify username/password |
| `Database does not exist` | Check the database name |
| `SSL required` | Add `?ssl=require` to the connection string |
| `Timeout` | Check firewall rules, security groups (AWS), or VPN |
| `Permission denied for table` | Run the GRANT statements above |

---

## Option 2: Via Metabase API

If you don't have direct database credentials but have Metabase access, you can use Metabase's API to run queries. This is a workaround — it's slower than direct DB access but works if Metabase is your only entry point.

### How It Works

```
User Question → LLM generates SQL → Metabase API executes SQL → Results back
```

Instead of connecting directly to PostgreSQL, we send the generated SQL to Metabase's `/api/dataset` endpoint which runs it against the database Metabase is connected to.

### What You Need

1. **Metabase URL**: e.g., `https://metabase.yourcompany.com`
2. **Metabase login credentials** (email + password) OR an **API key**
3. **Database ID** in Metabase (usually `1` for the first connected database)

### Step 1: Get Your Metabase API Token

```bash
# Get a session token by logging in:
curl -X POST https://your-metabase-url.com/api/session \
  -H "Content-Type: application/json" \
  -d '{"username": "your-email@company.com", "password": "your-password"}'

# Response:
# {"id": "your-session-token-here"}
```

Or if your Metabase has API keys enabled (Settings → Admin → API Keys), create one there.

### Step 2: Find Your Database ID

```bash
# List databases in Metabase:
curl https://your-metabase-url.com/api/database \
  -H "X-Metabase-Session: YOUR_SESSION_TOKEN"

# Look for your database in the response:
# [{"id": 1, "name": "College Production DB", ...}]
```

The `id` field is what you need (usually `1`).

### Step 3: Add Metabase Config to .env

```env
# Metabase connection (use INSTEAD of DATABASE_URL)
METABASE_URL=https://metabase.yourcompany.com
METABASE_USERNAME=your-email@company.com
METABASE_PASSWORD=your-password
METABASE_DATABASE_ID=1

# Keep DATABASE_URL as sqlite for fallback/schema caching
DATABASE_URL=sqlite+aiosqlite:///./mock.db
```

### Step 4: Create the Metabase Query Executor

Create a new file `app/db/metabase_client.py`:

```python
"""Metabase API client for executing SQL queries."""

import httpx
from typing import Any
from app.core.config import settings


class MetabaseClient:
    """Executes SQL queries via Metabase's API."""

    def __init__(self):
        self.base_url = settings.METABASE_URL.rstrip("/")
        self.database_id = settings.METABASE_DATABASE_ID
        self._session_token: str | None = None

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
        """
        token = await self._get_session_token()

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

        # Parse Metabase response format into list of dicts
        if "data" not in data:
            return []

        columns = [col["name"] for col in data["data"]["cols"]]
        rows = data["data"]["rows"]

        return [dict(zip(columns, row)) for row in rows]


# Singleton
metabase_client = MetabaseClient()
```

### Step 5: Update Config to Support Metabase

Add these to `app/core/config.py`:

```python
# Metabase (optional - alternative to direct DB)
METABASE_URL: Optional[str] = None
METABASE_USERNAME: Optional[str] = None
METABASE_PASSWORD: Optional[str] = None
METABASE_DATABASE_ID: int = 1
USE_METABASE: bool = False  # Set to True to use Metabase instead of direct DB
```

### Step 6: Update the Connection Layer

Modify `app/db/connection.py` to route through Metabase when configured:

```python
async def execute_read_query(sql: str) -> list[dict[str, Any]]:
    """Execute a read-only query — via direct DB or Metabase."""
    if settings.USE_METABASE and settings.METABASE_URL:
        from app.db.metabase_client import metabase_client
        return await metabase_client.execute_query(sql)

    # ... existing direct DB logic ...
```

### Step 7: Test with Metabase

```env
# In .env:
USE_METABASE=true
METABASE_URL=https://metabase.yourcompany.com
METABASE_USERNAME=your-email@company.com
METABASE_PASSWORD=your-password
METABASE_DATABASE_ID=1
```

```bash
uv run python -c "
import asyncio
from app.db.metabase_client import metabase_client

async def test():
    result = await metabase_client.execute_query('SELECT 1 as test')
    print(f'Metabase connected! Result: {result}')

asyncio.run(test())
"
```

### Metabase Limitations

| Aspect | Direct PostgreSQL | Via Metabase |
|--------|-------------------|--------------|
| Speed | Fast (direct connection) | Slower (HTTP API overhead) |
| Setup | Need DB credentials | Just Metabase login |
| Schema introspection | Full access | Limited (need to cache schema) |
| Query timeout | Configurable | Depends on Metabase settings |
| Rate limits | None | Metabase may limit API calls |
| Authentication | DB role | Metabase session token |

### Important Notes for Metabase

1. **Schema introspection won't work directly** — You'll need to manually fill in `annotations.yaml` with your real table/column names, or cache the schema on first run.

2. **Session tokens expire** — The client handles re-authentication automatically.

3. **Query results are limited** — Metabase may cap results at 2000 rows by default. Check your Metabase admin settings.

4. **SQL dialect** — Make sure the LLM generates SQL compatible with your actual database (PostgreSQL syntax). The prompts already handle this.

---

## Recommended Approach

| Scenario | Use |
|----------|-----|
| You have direct DB credentials | **Option 1** (Direct PostgreSQL) |
| You only have Metabase access | **Option 2** (Metabase API) |
| Testing before production | Keep SQLite mock DB |
| You want both for comparison | Set up both, toggle with `USE_METABASE` env var |

### Switching Between Modes

```env
# Mock DB (default for development)
DATABASE_URL=sqlite+aiosqlite:///./mock.db
USE_METABASE=false

# Direct PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
USE_METABASE=false

# Via Metabase
USE_METABASE=true
METABASE_URL=https://metabase.company.com
METABASE_USERNAME=email
METABASE_PASSWORD=password
METABASE_DATABASE_ID=1
```

---

## After Connecting: Update Schema Annotations

Once you're connected to the real database, you need to update `app/schema/annotations.yaml` so the LLM knows what your tables mean. Run the discovery script from Step 6 (Option 1), then update the YAML with:

1. Your real table names
2. Domain groupings (which tables belong to attendance, academics, etc.)
3. Column descriptions (especially non-obvious ones)
4. Important notes (e.g., "Use StudentAttendance table, not LegacyAttendance")
5. Key relationships (foreign keys, common JOINs)

This is the most important step for accuracy — the better your annotations, the better the chatbot's SQL generation.
