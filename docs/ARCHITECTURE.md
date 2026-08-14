# Architecture Overview

A high-level view of how the College Chatbot works, designed for anyone wanting to contribute or understand the codebase.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                                 │
│                                                                        │
│  ┌────────────────────┐         ┌─────────────────────────────────┐  │
│  │  Next.js Frontend   │────────▶│  FastAPI Backend (Port 8000)     │  │
│  │  (Port 3000)        │◀────────│                                   │  │
│  │                      │  HTTP   │  POST /api/chat                  │  │
│  │  - Chat interface    │         │  GET  /api/logs                  │  │
│  │  - Charts & Export   │         │  GET  /health                    │  │
│  │  - Conversations     │         │                                   │  │
│  └────────────────────┘         └──────────────┬────────────────────┘  │
└──────────────────────────────────────────────────┼──────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                    PIPELINE ENGINE                            │
                    │                                                                │
                    │  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐   │
                    │  │ 1. Domain    │──▶│ 2. Schema     │──▶│ 3. SQL          │   │
                    │  │ Classifier   │   │ Context       │   │ Generator       │   │
                    │  │              │   │ Builder       │   │                 │   │
                    │  │ "What domain │   │               │   │ NL → SQL        │   │
                    │  │  is this     │   │ Loads only    │   │ with schema     │   │
                    │  │  question?"  │   │ relevant      │   │ context +       │   │
                    │  │              │   │ tables +      │   │ known values    │   │
                    │  │ → attendance │   │ relationships │   │                 │   │
                    │  │ → academics  │   │ + enum values │   │ → SELECT ...    │   │
                    │  │ → coding     │   │               │   │                 │   │
                    │  └─────────────┘   └──────────────┘   └────────┬────────┘   │
                    │                                                    │            │
                    │  ┌─────────────┐   ┌──────────────┐   ┌────────▼────────┐   │
                    │  │ 6. Response  │◀──│ 5. Query      │◀──│ 4. SQL          │   │
                    │  │ Formatter    │   │ Executor      │   │ Validator       │   │
                    │  │              │   │               │   │                 │   │
                    │  │ - Single val │   │ Metabase API  │   │ - SELECT only   │   │
                    │  │   → sentence │   │ or Direct DB  │   │ - No DDL/DML    │   │
                    │  │ - Multi-row  │   │               │   │ - Length limit   │   │
                    │  │   → table    │   │ + Timeout     │   │ - Single stmt   │   │
                    │  │ - Empty      │   │               │   │                 │   │
                    │  │   → retry    │   │               │   │ If invalid:     │   │
                    │  └─────────────┘   └──────────────┘   │ retry with      │   │
                    │                                         │ error context   │   │
                    │         ┌───────────────────────┐       └─────────────────┘   │
                    │         │ SELF-HEALING RETRY     │                              │
                    │         │                         │                              │
                    │         │ If 0 results:          │                              │
                    │         │ 1. Feed error to LLM   │                              │
                    │         │ 2. LLM tries looser    │                              │
                    │         │    query               │                              │
                    │         │ 3. Up to 3 attempts    │                              │
                    │         └───────────────────────┘                              │
                    └────────────────────────────────────────────────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                    DATA LAYER                                  │
                    │                                                                │
                    │  ┌─────────────────┐         ┌──────────────────────────┐    │
                    │  │ Schema Cache     │         │ Database Access           │    │
                    │  │                   │         │                            │    │
                    │  │ annotations.yaml  │         │ Option A: Metabase API    │    │
                    │  │ schema_cache.yaml │         │ Option B: Direct Postgres │    │
                    │  │                   │         │ Option C: SQLite (mock)   │    │
                    │  │ - Table columns   │         │                            │    │
                    │  │ - Relationships   │         └──────────────────────────┘    │
                    │  │ - Domain groups   │                                          │
                    │  │ - Enum values     │         ┌──────────────────────────┐    │
                    │  │ - Center names    │         │ LLM Provider              │    │
                    │  │ - JOIN patterns   │         │                            │    │
                    │  └─────────────────┘         │ Google Gemini 2.5 Flash   │    │
                    │                               │ (swappable via factory)    │    │
                    │                               └──────────────────────────┘    │
                    └────────────────────────────────────────────────────────────────┘
```

---

## Request Flow (Step by Step)

```
User: "Show me batch 24 students with attendance for 4th semester"
  │
  ▼
┌─ 1. INPUT VALIDATION ────────────────────────────────────────────────┐
│  - Check length (max 500 chars)                                        │
│  - Rate limit (10 req/min per session)                                 │
│  - Get/create conversation state                                       │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 2. DOMAIN CLASSIFICATION (LLM call #1) ─────────────────────────────┐
│  Prompt: "Classify this question into a domain"                         │
│  Result: "attendance"                                                    │
│  Time: ~3-5 seconds                                                      │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 3. SCHEMA CONTEXT BUILDING (local, instant) ────────────────────────┐
│  - Load annotations.yaml → filter to "attendance" domain tables        │
│  - Load schema_cache.yaml → add center names, enums, JOIN patterns     │
│  - Build formatted prompt with table descriptions + relationships       │
│  - Result: ~2KB of focused schema context                                │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 4. SQL GENERATION (LLM call #2) ────────────────────────────────────┐
│  Prompt: question + schema context + rules + known values               │
│  Result: SELECT s.name, ... FROM "Student" JOIN "Attendance" ...         │
│  Time: ~3-5 seconds                                                      │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 5. SQL VALIDATION (local, instant) ─────────────────────────────────┐
│  - Parse with sqlparse                                                   │
│  - Check: single statement, SELECT only, no forbidden keywords           │
│  - If invalid → retry with error context                                 │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 6. QUERY EXECUTION (Metabase API or Direct DB) ─────────────────────┐
│  - Send SQL to Metabase /api/dataset endpoint                            │
│  - Parse response into list of dicts                                     │
│  - Time: ~1-3 seconds                                                    │
│                                                                           │
│  If 0 results → RETRY (back to step 4 with feedback)                    │
│  "Your query returned 0 results. Try looser filters..."                  │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 7. RESPONSE FORMATTING (LLM call #3 + local) ──────────────────────┐
│  - If aggregate (COUNT/AVG): LLM generates natural sentence              │
│  - If data rows: LLM generates 1-line intro + local table formatter      │
│  - Result: "Found 171 students:\n\n| Name | Email | Attendance % |"      │
│  Time: ~3-5 seconds                                                      │
└──────────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─ 8. LOG + RESPOND ───────────────────────────────────────────────────┐
│  - Log query to query_logs.json (question, SQL, timing, row count)       │
│  - Store conversation context for follow-ups                             │
│  - Return JSON response to frontend                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**Total time per query: ~10-20 seconds** (dominated by 2-3 LLM calls at ~5s each)

---

## File-by-File Map

### Core Pipeline
| File | What it does |
|------|-------------|
| `app/core/pipeline.py` | **The brain** — orchestrates the entire NL→SQL flow with retry logic |
| `app/core/models.py` | Pydantic models: ChatRequest, ChatResponse, PipelineResult |
| `app/core/config.py` | All env vars loaded into typed Settings object |
| `app/core/conversation.py` | In-memory conversation state for follow-ups/clarifications |
| `app/core/logger.py` | JSON-lines query logger for audit trail |
| `app/core/rate_limiter.py` | Sliding window rate limiter |

### LLM Layer
| File | What it does |
|------|-------------|
| `app/llm/base.py` | Abstract interface — implement this to add new LLM providers |
| `app/llm/gemini_provider.py` | Google Gemini implementation with retry + backoff |
| `app/llm/factory.py` | Reads `LLM_PROVIDER` env var, returns correct provider |
| `app/llm/prompts/templates.py` | All prompt templates (classification, SQL gen, response, ambiguity) |

### Schema & Context
| File | What it does |
|------|-------------|
| `app/schema/annotations.yaml` | Domain groupings, table descriptions, column descriptions, notes |
| `app/schema/schema_cache.yaml` | Cached values: center names, batch names, enums, JOIN patterns |
| `app/schema/db_relationships.yaml` | **Complete FK relationship graph** (116 relationships from Prisma) |
| `app/schema/context_builder.py` | Merges annotations + cache → builds the prompt context string |
| `app/schema/introspector.py` | Live DB metadata reader (used for mock DB, skipped for Metabase) |

### Database
| File | What it does |
|------|-------------|
| `app/db/connection.py` | Routes queries: Metabase API vs Direct DB vs SQLite |
| `app/db/metabase_client.py` | HTTP client for Metabase's /api/dataset endpoint |
| `app/db/mock_schema.sql` | SQLite DDL for local development |
| `app/db/seed_data.sql` | Sample data for mock DB |

### API & Formatter
| File | What it does |
|------|-------------|
| `app/api/chat.py` | POST /api/chat — input validation, rate limit, pipeline, logging |
| `app/api/logs.py` | GET /api/logs — paginated query audit viewer |
| `app/formatter/response_formatter.py` | Formats raw results into markdown tables/sentences |
| `app/guardrails/sql_validator.py` | sqlparse-based SELECT-only enforcement |

### Frontend
| File | What it does |
|------|-------------|
| `frontend/src/app/page.tsx` | Main layout — sidebar + chat area |
| `frontend/src/components/ChatArea.tsx` | Message list, auto-scroll, loading indicator |
| `frontend/src/components/ChatMessage.tsx` | Individual message — markdown, SQL viewer, chart, export |
| `frontend/src/components/ChartRenderer.tsx` | Bar/line/pie/area chart visualization |
| `frontend/src/hooks/useConversations.ts` | Conversation state management with backend sync |
| `frontend/src/lib/api.ts` | Backend API integration |

---

## How the Schema Context System Works

The LLM needs to know the database structure to generate correct SQL. Here's how we feed it:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCHEMA KNOWLEDGE STACK                          │
│                                                                    │
│  Layer 1: db_relationships.yaml (COMPLETE FK graph)               │
│  ─────────────────────────────────────────────────                │
│  All 116 foreign key relationships from the Prisma schema.        │
│  This tells the LLM HOW to JOIN tables correctly.                 │
│                                                                    │
│  Layer 2: annotations.yaml (DOMAIN knowledge)                     │
│  ─────────────────────────────────────────────────                │
│  Tables grouped by domain (attendance, academics, etc.)            │
│  Column descriptions, important notes, canonical sources.          │
│                                                                    │
│  Layer 3: schema_cache.yaml (KNOWN VALUES)                        │
│  ─────────────────────────────────────────────────                │
│  Actual center names, batch names, enum values.                    │
│  Common query patterns with working SQL examples.                  │
│  Table quoting rules for PostgreSQL.                               │
│                                                                    │
│  Layer 4: SQL Generation Prompt (RULES)                           │
│  ─────────────────────────────────────────────────                │
│  PostgreSQL-specific rules: double-quote tables, ILIKE,            │
│  semester date filtering patterns, NULLIF for division.            │
└─────────────────────────────────────────────────────────────────┘
```

When a query comes in, only the **relevant layers** are included in the prompt (filtered by domain), keeping token usage low while maintaining accuracy.

---

## Key Design Decisions

### 1. Self-Healing Retry
When a query returns 0 results, the pipeline doesn't give up. It feeds the failed SQL back to the LLM with context like "query returned 0 results, try looser filters" and the LLM generates a better query. Up to 3 attempts.

### 2. Schema Caching (No Live Introspection)
For Metabase mode, we skip live schema introspection (which was making 74+ API calls). Instead, we use pre-cached YAML files that contain everything the LLM needs. Update these files when the schema changes.

### 3. LLM-Agnostic Design
The `BaseLLMProvider` abstract class means swapping Gemini for GPT-4 or Claude is just:
1. Write a new provider class
2. Register in factory.py
3. Change `LLM_PROVIDER` env var

### 4. Defense in Depth (Security)
```
Layer 1: SQL Validator (application)   → Only SELECT allowed
Layer 2: Metabase API (infrastructure) → Uses Metabase's own permissions
Layer 3: DB Role (if direct)           → Read-only PostgreSQL role
```

### 5. Conversation Context
Each session stores the last question + SQL + answer. This enables follow-up questions like "show me their emails" to reference what was just discussed.

---

## How to Contribute

### Adding a New Domain
1. Add domain definition in `app/schema/annotations.yaml` under `domains:`
2. Add table descriptions under `tables:`
3. Add relationships in `app/schema/db_relationships.yaml`
4. Test with a few questions to verify the LLM picks up the new domain

### Improving Query Accuracy
1. Add more patterns to `IMPORTANT PATTERNS` in `app/llm/prompts/templates.py`
2. Add common SQL examples in `schema_cache.yaml` under `common_queries`
3. Add new known values (center names, enum values, etc.) to `schema_cache.yaml`

### Adding a New LLM Provider
1. Create `app/llm/your_provider.py` implementing `BaseLLMProvider`
2. Add to `app/llm/factory.py`
3. Set `LLM_PROVIDER=your_provider` in `.env`

### Updating for Schema Changes
When the Prisma schema changes:
1. Re-run the FK discovery script (or check Metabase metadata)
2. Update `app/schema/db_relationships.yaml`
3. Update `app/schema/annotations.yaml` with new table/column descriptions
4. Update `app/schema/schema_cache.yaml` with new enum values if any
