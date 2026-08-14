# System Architecture

Complete technical architecture of the NL→SQL College Chatbot system.

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUESTION (NL)                      │
│         (English, Hindi, Hinglish - any language)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │   DOMAIN CLASSIFICATION        │
        │  (Gemini LLM)                  │
        │  → attendance/academics/       │
        │    students/general            │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  BUILD SCHEMA CONTEXT          │
        │  ✓ Only 10 allowed tables      │
        │  ✓ Domain-specific tables      │
        │  ✓ Relationship graph          │
        │  ✓ Column descriptions         │
        │  ✓ Sample data values          │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  AMBIGUITY ASSESSMENT          │
        │  (Optional: for vague Qs)      │
        │  → Ask clarifying question     │
        │  → Wait for user response      │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  SQL GENERATION                │
        │  (Gemini LLM)                  │
        │  ✓ PostgreSQL only             │
        │  ✓ Business filters applied    │
        │  ✓ Only SELECT queries         │
        │  Attempt: 1 of 3               │
        └────────────┬───────────────────┘
                     │
                     ▼
        ┌────────────────────────────────┐
        │  SQL VALIDATION                │
        │  ✓ Single statement only       │
        │  ✓ No DML/DDL keywords         │
        │  ✓ Only allowed tables         │
        │  ✓ Mandatory filters present   │
        │  ✓ Valid syntax                │
        └────────────┬───────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼ VALID                   ▼ INVALID
    EXECUTE QUERY            Retry (attempt++)
    (PostgreSQL)             (max 3 attempts)
         │
         ├─→ 0 RESULTS: Retry with feedback
         ├─→ RESULTS ✓: Success
         └─→ TIMEOUT (30s): Error to user
             │
             ▼
    FORMAT RESPONSE
    ✓ Natural language
    ✓ Data table
    ✓ Charts (optional)
             │
             ▼
   ┌──────────────────┐
   │  USER RESPONSE   │
   │  (Answer + SQL)  │
   └──────────────────┘
```

## Component Architecture

### 1. FastAPI Backend (app/main.py)

**Routes:**
- `POST /api/chat` - Main query endpoint
- `GET /api/conversations` - Conversation history
- `GET /api/logs` - Query audit logs
- `GET /health` - Health check

**Middleware:**
- Rate limiter (10 req/min per session)
- CORS handler
- Error handler
- Audit logger

### 2. Domain Classification (app/llm/gemini_provider.py)

**Purpose:** Route question to correct domain

**Domains:**
- `attendance` - Presence, absence, tardy records
- `academics` - Exams, marks, grades, subjects
- `students` - Student info, enrollment, batches
- `general` - Cross-domain questions
- `out_of_scope` - REJECT (weather, jokes, unrelated)

### 3. Schema Context Builder (app/schema/context_builder.py)

**Inputs:**
- Domain (from classification)
- Allowed tables list
- Table relationships
- Column descriptions

**Process:**
1. Load domain-specific tables from annotations.yaml
2. Filter to only 10 allowed tables
3. Build foreign key relationships
4. Add sample values and enum options
5. Format for LLM consumption

**Output:** Context string (1500-3000 chars)

### 4. Ambiguity Detection (app/llm/gemini_provider.py)

**Triggers for:** Questions with ≤3 words without context

**Example:**
- Q: "How many?"
- A: "How many students? Attendance records? Classes?"

### 5. SQL Generation (app/llm/gemini_provider.py)

**LLM Prompt:** templates.py::SQL_GENERATION_PROMPT

**Includes:**
1. Role definition (SQL Generator)
2. Forbidden keywords list
3. Allowed tables only
4. Business filter examples
5. PostgreSQL syntax rules
6. Sample queries with filters
7. Schema context
8. User question

**Output:** Raw SQL string (no markdown)

### 6. SQL Validation (app/guardrails/sql_validator.py)

**Checks:**
1. Single statement only
2. SELECT only (no DML/DDL)
3. No fake queries (must have FROM)
4. Max 2000 chars
5. No forbidden keywords
6. No dangerous patterns
7. Only allowed tables
8. Business filters present

**Output:** ValidationResult(is_valid, error_message, sanitized_sql)

### 7. Query Execution (app/db/connection.py)

**Process:**
1. Create read-only async connection
2. Set statement timeout (30 seconds)
3. Execute SELECT only
4. Fetch results (max 10,000 rows)
5. Close connection

**Database Role:** chatbot_reader (SELECT only)

**Error Handling:**
- Network errors → Retry once
- Syntax errors → Include in feedback
- Timeout → Return to user immediately
- Logic errors (0 results) → Retry with feedback

### 8. Retry Logic (app/core/pipeline.py)

**Retry Loop:**
```
Attempt 1: Generate SQL
  ├─→ Valid + Results ✓ → Return
  ├─→ Valid + 0 Results → Try again with feedback
  └─→ Invalid + Error → Try again with feedback

Attempt 2: Generate SQL with previous error
  ├─→ Valid + Results ✓ → Return
  ├─→ Valid + 0 Results → Try again with feedback
  └─→ Invalid + Error → Try again with feedback

Attempt 3: Generate SQL (last try)
  ├─→ Any result → Return as-is
  └─→ Any error → Return error to user
```

### 9. Response Formatting (app/formatter/response_formatter.py)

**Input:** Results from database

**Output Types:**
1. **Single Value:** Natural language sentence
2. **Multiple Rows:** Table format
3. **Large Result Sets:** Paginated
4. **Charts:** For trending/comparative data

### 10. Conversation State (app/core/conversation.py)

**Purpose:** Track multi-turn conversations

**Storage:**
- Session ID (UUID)
- Question history
- Context for follow-ups
- Conversation lifetime: 30 minutes

## Data Flow Diagram

```
┌──────────────────────────────────────┐
│      PostgreSQL Database             │
│    (10 allowed tables)               │
│    - Teacher, Center, Batch          │
│    - School, Subject, Semester       │
│    - Division, Class, Attendance     │
│    - Student                         │
└──────────────────────────────────────┘
         ↑
         │ (async SELECT only)
         │
┌────────┴──────────────────────────────────┐
│     PostgreSQL Connection Pool            │
│     (read-only role: chatbot_reader)      │
│     (timeout: 30s per query)              │
└────────┬──────────────────────────────────┘
         ↑
         │ (validated SQL)
         │
┌────────┴──────────────────────────────────┐
│  SQL Validator (sql_validator.py)         │
│  ✓ Syntax check                           │
│  ✓ Single statement only                  │
│  ✓ SELECT only (no DML/DDL)               │
│  ✓ Allowed tables only                    │
│  ✓ Business filters present               │
└────────┬──────────────────────────────────┘
         ↑
         │ (raw SQL)
         │
┌────────┴──────────────────────────────────┐
│    LLM SQL Generator (Gemini)             │
│    Input: Question + Schema Context       │
│    Output: PostgreSQL SELECT statement    │
└────────┬──────────────────────────────────┘
         ↑
         │ (schema context)
         │
┌────────┴──────────────────────────────────┐
│  Schema Context Builder                   │
│  ├─ Load 10 allowed tables                │
│  ├─ Domain-specific filtering             │
│  ├─ Relationship graph                    │
│  ├─ Business filter rules                 │
│  └─ Sample data values                    │
└────────┬──────────────────────────────────┘
         ↑
         │ (domain)
         │
┌────────┴──────────────────────────────────┐
│    Domain Classifier (Gemini)             │
│    Input: User question (any language)    │
│    Output: Domain (attendance/academics..)
└────────┬──────────────────────────────────┘
         ↑
         │
    ┌────┴────────────────┐
    │  User Question      │
    │  • English          │
    │  • Hindi            │
    │  • Hinglish         │
    └─────────────────────┘
```

## Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **API** | FastAPI + Uvicorn | Async, high performance |
| **LLM** | Google Gemini 2.5 Flash | Swappable via factory pattern |
| **Database** | PostgreSQL + asyncpg | Async driver, connection pooling |
| **ORM** | SQLAlchemy | Schema introspection |
| **SQL Parsing** | sqlparse | Validation and analysis |
| **Schema Cache** | YAML + Python dicts | In-memory, fast lookup |
| **Frontend** | Next.js + React + Tailwind | Beautiful chat UI |
| **Containers** | Docker + Docker Compose | Multi-container orchestration |
| **Testing** | pytest | 80+ test cases |

## Performance Characteristics

**Latency Budget (P90):**
- Domain classification: 200ms
- Schema context building: 100ms
- SQL generation (LLM call): 1000ms
- SQL validation: 50ms
- Query execution: 500ms
- Response formatting: 100ms
- **Total: ~2 seconds**

**Throughput:**
- 10 requests/minute per session (rate limited)
- Connection pool: 5 connections
- Max 10,000 rows per query
- Max 2000 chars per SQL query

**Resource Usage:**
- Memory per request: ~50MB
- Memory per session: ~100MB (conversation history)
- Database connections: Pooled, max 5 per backend instance

## Scaling Considerations

1. **Horizontal:** Multiple FastAPI instances behind load balancer
2. **Caching:** Schema context cached in memory, invalidated hourly
3. **Database:** Read replicas for high-volume scenarios
4. **Sessions:** Conversation state stored in Redis (optional)
5. **Monitoring:** Prometheus metrics for LLM calls, DB queries, errors

## File Organization

```
app/
├── main.py                    # FastAPI entrypoint
├── api/
│   ├── chat.py                # POST /api/chat
│   ├── conversations.py       # Conversation routes
│   └── logs.py                # Audit log routes
├── core/
│   ├── pipeline.py            # Main orchestration
│   ├── models.py              # Request/response schemas
│   ├── conversation.py        # State management
│   ├── logger.py              # Audit logging
│   └── rate_limiter.py        # Rate limiting
├── llm/
│   ├── base.py                # Abstract provider
│   ├── gemini_provider.py     # Gemini implementation
│   ├── factory.py             # Provider factory
│   └── prompts/
│       └── templates.py       # Prompt templates
├── db/
│   ├── connection.py          # DB connection & execution
│   └── metabase_client.py     # Metabase integration
├── schema/
│   ├── introspector.py        # Live schema reader
│   ├── context_builder.py     # Context generator
│   ├── annotations.yaml       # Table metadata
│   ├── db_relationships.yaml  # FK graph
│   └── schema_cache.yaml      # Cached values
├── guardrails/
│   └── sql_validator.py       # SQL validation
└── formatter/
    └── response_formatter.py  # Response formatting
```

## Error Handling Strategy

**User-Facing Errors (Safe to Show):**
- "I couldn't find any data matching that description"
- "Could you please be more specific?"
- "I can only answer questions about the college database"

**Logged Errors (Never Show):**
- Full SQL error messages (contain schema info)
- Database connection details
- Stack traces
- Internal error paths

**Retry Triggers:**
- Query execution timeout (automatic)
- 0 results returned (automatic, up to 3 times)
- Validation error (automatic, different approach)
- Business rule violation (automatic)

**Hard Failures (Return to User):**
- All 3 retries exhausted
- Database unavailable
- LLM unavailable
- Input validation failed

## Future Enhancements

1. **Multi-language:** Detect/preserve language preference per session
2. **Charts:** Auto-generate charts for comparative data
3. **Explanations:** "Here's how I understood your question"
4. **Suggestions:** "You might also want to know..."
5. **Export:** Download results as CSV/Excel
6. **Saved Queries:** "Save this query for later"
7. **Benchmarking:** Track accuracy and speed metrics
