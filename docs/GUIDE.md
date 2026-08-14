# Developer Guide - College NL→SQL Chatbot

Complete technical guide for understanding, extending, and maintaining the chatbot system.

**Last Updated:** 2026-08-07 | **Status:** Production Ready | **Phase:** 1 (10 Tables)

---

## Table of Contents
## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [System Components](#system-components)
4. [NL→SQL Pipeline](#nlsql-pipeline)
5. [Security Model](#security-model)
6. [Development Setup](#development-setup)
7. [Adding Features](#adding-features)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

---

## Architecture Overview

### High-Level Design

```
┌──────────────────────────────────────────────────────────────┐
│                    Next.js Frontend (React)                  │
│                    Chat UI + Results Display                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼ HTTPS
┌──────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Async)                    │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  API Routes (/api/chat, /api/conversations, /api/logs)  │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  Domain Classification → Ambiguity Detection             │ │
│  │  (Gemini LLM)                                            │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  Schema Context Builder                                 │ │
│  │  (Only 10 allowed tables)                               │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  SQL Generation (Gemini LLM)                            │ │
│  │  With mandatory business filters                        │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  SQL Validation (7 checks)                              │ │
│  │  • Single statement only                                │ │
│  │  • SELECT only (no DML/DDL)                             │ │
│  │  • Allowed tables only                                  │ │
│  │  • Business filters present                             │ │
│  │  • No fake queries                                      │ │
│  │  • No forbidden patterns                                │ │
│  │  • Valid syntax                                         │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  Retry Logic (Up to 3 attempts)                         │ │
│  │  With feedback from previous failures                   │ │
│  └────────────────────┬────────────────────────────────────┘ │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  Response Formatting                                    │ │
│  │  (Natural language + Table + Charts)                    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼ asyncpg
┌──────────────────────────────────────────────────────────────┐
│               PostgreSQL Database (Read-Only)                │
│                                                               │
│  10 Allowed Tables:                                          │
│  Teacher, Center, Batch, School, Subject, Semester,         │
│  Division, Class, Attendance, Student                        │
│                                                               │
│  With 4 Mandatory Filters:                                   │
│  • Exclude PW Skills centers                                │
│  • Exclude TEST Center                                      │
│  • Active students only                                     │
│  • No dummy emails                                          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Scoped by Design** - Only 10 tables, no hallucination
2. **Secure by Default** - Business filters always applied
3. **Fail-Safe** - Multiple validation layers
4. **Resilient** - Retry with feedback on failure
5. **Observable** - Audit logging of all queries
6. **Maintainable** - Clear separation of concerns

---

## Database Schema

### 10 Allowed Tables

#### 1. Student
```sql
CREATE TABLE "Student" (
  id UUID PRIMARY KEY,
  name VARCHAR,
  email VARCHAR UNIQUE,
  phone VARCHAR UNIQUE,
  gender ENUM, -- MALE, FEMALE
  is_active BOOLEAN, -- FILTER: = true
  enrollment_id VARCHAR UNIQUE,
  center_id UUID, -- FK to Center (FILTER center name)
  batch_id UUID, -- FK to Batch
  school_id UUID, -- FK to School
  division_id UUID, -- FK to Division
  semester_id UUID, -- FK to Semester
  joining_date TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Mandatory Filters:**
- `WHERE is_active = true`
- `AND email NOT LIKE '%dummyemail%'`

#### 2. Center
```sql
CREATE TABLE "Center" (
  id UUID PRIMARY KEY,
  name VARCHAR, -- FILTER: NOT LIKE '%PW Skills%' AND != 'TEST Center'
  location VARCHAR,
  code INT UNIQUE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Mandatory Filters:**
- `WHERE name NOT LIKE '%PW Skills%'`
- `AND name != 'TEST Center'`

**Included Centers:**
- IOI Bengaluru, IOI Delhi, IOI Noida, IOI Pune, IOI Patna, IOI Lucknow, IOI Indore

**Excluded Centers:**
- PW Skills Bangalore, PW Skills Noida, PW Skills Lucknow, etc.
- TEST Center

#### 3. Batch
```sql
CREATE TABLE "Batch" (
  id UUID PRIMARY KEY,
  name VARCHAR, -- e.g., "23", "24", "25"
  center_id UUID, -- FK to Center
  school_id UUID, -- FK to School
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 4. School
```sql
CREATE TABLE "School" (
  id UUID PRIMARY KEY,
  name VARCHAR, -- e.g., "SOT", "SOM"
  center_id UUID, -- FK to Center (UNIQUE constraint: center_id + name)
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 5. Division
```sql
CREATE TABLE "Division" (
  id UUID PRIMARY KEY,
  code VARCHAR, -- e.g., "A", "B", "C"
  center_id UUID, -- FK to Center
  batch_id UUID, -- FK to Batch
  school_id UUID, -- FK to School
  current_semester UUID, -- FK to Semester (UNIQUE)
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 6. Semester
```sql
CREATE TABLE "Semester" (
  id UUID PRIMARY KEY,
  number INT, -- 1, 2, 3, 4, ...
  division_id UUID, -- FK to Division
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 7. Subject
```sql
CREATE TABLE "Subject" (
  id UUID PRIMARY KEY,
  name VARCHAR,
  semester_id UUID, -- FK to Semester
  credits INT,
  code VARCHAR,
  teacher_id UUID, -- FK to Teacher
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 8. Teacher
```sql
CREATE TABLE "Teacher" (
  id UUID PRIMARY KEY,
  name VARCHAR,
  email VARCHAR UNIQUE,
  phone VARCHAR UNIQUE,
  role VARCHAR, -- e.g., "TEACHER"
  gender ENUM, -- MALE, FEMALE
  designation VARCHAR,
  center_id UUID, -- FK to Center
  is_active BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

#### 9. Class
```sql
CREATE TABLE "Class" (
  id UUID PRIMARY KEY,
  lecture_number VARCHAR,
  subject_id UUID, -- FK to Subject
  division_id UUID, -- FK to Division
  teacher_id UUID, -- FK to Teacher
  room_id UUID,
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Indexes:**
- (division_id, start_date)
- (subject_id)
- (teacher_id)

#### 10. Attendance
```sql
CREATE TABLE "Attendance" (
  id UUID PRIMARY KEY,
  student_id UUID, -- FK to Student
  class_id UUID, -- FK to Class
  status VARCHAR, -- PRESENT, ABSENT, LATE
  successful_scan_count INT,
  marked_by VARCHAR, -- MANUAL, SCAN
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Constraint:** UNIQUE(student_id, class_id)

### Relationships

```
Center
├─ Batch
│  └─ Division
│     ├─ Semester
│     │  └─ Subject
│     │     └─ Class ← Attendance → Student
│     └─ Student ← Attendance → Class
├─ School
│  ├─ Batch
│  └─ Student
└─ Teacher
   └─ Subject
      └─ Class
         └─ Attendance
```

### Common JOIN Patterns

#### Students by Center
```sql
SELECT s.* FROM "Student" s
JOIN "Center" c ON s.center_id = c.id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
  AND c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
```

#### Attendance by Student
```sql
SELECT s.name, COUNT(*) as classes,
       COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) as present
FROM "Student" s
LEFT JOIN "Attendance" a ON s.id = a.student_id
LEFT JOIN "Class" cl ON a.class_id = cl.id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
GROUP BY s.id, s.name
```

#### Classes by Teacher
```sql
SELECT t.name, COUNT(cl.id) as class_count
FROM "Teacher" t
LEFT JOIN "Class" cl ON t.id = cl.teacher_id
WHERE t.is_active = true
GROUP BY t.id, t.name
```

---

## System Components

### 1. API Layer (`app/api/`)

**Chat Endpoint:** `POST /api/chat`

```python
# app/api/chat.py
@router.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main entry point for NL→SQL pipeline.
    
    Flow:
    1. Validate question (max 500 chars)
    2. Get or create conversation
    3. Run pipeline (classify → schema → SQL → validate → execute → format)
    4. Return response
    """
    question = request.question.strip()
    conversation_id = request.conversation_id
    
    # Run pipeline
    result = await run_pipeline(question, conversation_id)
    
    return ChatResponse(
        answer=result.answer,
        sql=result.sql,
        domain=result.domain,
        execution_time_ms=result.execution_time_ms
    )
```

### 2. Pipeline Orchestration (`app/core/pipeline.py`)

**Main Function:** `run_pipeline(question, conversation_context, provider)`

```python
async def run_pipeline(
    question: str,
    conversation_context: Optional[str] = None,
    provider: Optional[BaseLLMProvider] = None,
) -> PipelineResult:
    """
    Orchestrates the full NL→SQL pipeline with self-healing retry.
    
    Steps:
    1. Domain Classification (which domain?)
    2. Schema Context Building (get relevant schema)
    3. Ambiguity Detection (is question clear?)
    4. SQL Generation (LLM generates SQL)
    5. SQL Validation (7-layer check)
    6. Query Execution (run on database)
    7. Response Formatting (format results)
    8. Retry Logic (if failed, try again up to 3 times)
    """
```

**Key Features:**
- Retry loop (up to 3 attempts)
- Feedback from previous failures
- Timeout protection
- Error aggregation

### 3. LLM Integration (`app/llm/`)

**Base Interface:** `BaseLLMProvider`

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    async def classify_domain(self, question: str) -> str:
        """Returns: attendance|academics|coding|clubs|..."""
        pass
    
    @abstractmethod
    async def generate_sql(self, question: str, schema_context: str) -> str:
        """Returns: PostgreSQL SELECT statement"""
        pass
    
    @abstractmethod
    async def generate_response(self, question: str, sql: str, results: list) -> str:
        """Returns: Natural language response"""
        pass
```

**Implementation:** `GeminiProvider`

```python
class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
    
    async def generate_sql(self, question: str, schema_context: str) -> str:
        prompt = SQL_GENERATION_PROMPT.format(
            schema_context=schema_context,
            question=question
        )
        response = await self.client.messages.create(
            model=self.model,
            prompt=prompt,
            max_tokens=500
        )
        return response.text.strip()
```

**Key Features:**
- Abstract interface for provider swapping
- Factory pattern for initialization
- Async/await for non-blocking calls

### 4. Schema Context Builder (`app/schema/context_builder.py`)

**Main Function:** `build_schema_context(domain)`

Builds the LLM prompt context by:

1. Loading domain-specific tables (filtered to only 10)
2. Building foreign key relationship graph
3. Adding table and column descriptions
4. Including sample data values
5. Adding business filter rules

**Output Example:**
```
SCHEMA CONTEXT:

Available Tables:
1. "Student" (id, name, email, is_active, center_id, ...)
   - Student enrollment and organizational info
   - is_active: true=currently enrolled, false=dropped
   - email: Filter out '%dummyemail%'

2. "Center" (id, name, location, code)
   - Physical campus locations
   - name: Filter out '%PW Skills%' and 'TEST Center'

...

Relationships:
- Student.center_id -> Center.id
- Student.batch_id -> Batch.id
- Student.division_id -> Division.id
...

Sample Values:
- Center names: IOI Bengaluru, IOI Delhi, IOI Noida, ...
- Batch names: 23, 24, 25
- Attendance status: PRESENT, ABSENT, LATE
...

Mandatory Filters:
- Students: is_active=true AND email NOT LIKE '%dummyemail%'
- Centers: name NOT LIKE '%PW Skills%' AND name != 'TEST Center'
```

### 5. SQL Validation (`app/guardrails/sql_validator.py`)

**Main Function:** `validate_sql(sql, check_business_filters=True)`

Performs 7 layers of validation:

1. **Length Check** - Max 2000 chars
2. **Empty Check** - Not null/empty
3. **Multiple Statements** - Only one statement allowed
4. **Statement Type** - SELECT or WITH...SELECT only
5. **Forbidden Keywords** - No INSERT/UPDATE/DELETE/DROP/etc
6. **Forbidden Patterns** - No dangerous patterns
7. **Allowed Tables Only** - NEW: Only 10 allowed tables
8. **Business Filters** - NEW: Required filters present

```python
def validate_sql(sql: str, check_business_filters: bool = True) -> ValidationResult:
    # Check 1-6: Original validation
    # Check 7: NEW - Allowed tables only
    result = _check_allowed_tables_only(sql)
    if not result.is_valid:
        return result
    
    # Check 8: NEW - Business filters
    if check_business_filters:
        result = _check_business_filters(sql)
        if not result.is_valid:
            return result
    
    return ValidationResult(is_valid=True, sanitized_sql=sql)
```

### 6. Database Connection (`app/db/connection.py`)

**Main Function:** `execute_read_query(sql)`

```python
async def execute_read_query(sql: str) -> list[dict]:
    """
    Execute a read-only query safely.
    
    Features:
    - Async connection pooling
    - 30-second timeout
    - Max 10,000 rows
    - Automatic retry on transient errors
    - Connection cleanup
    """
    async with get_db_connection() as conn:
        # Set statement timeout
        await conn.execute("SET statement_timeout TO 30000")
        
        # Execute query
        rows = await conn.fetch(sql)
        
        # Limit results
        return rows[:10000]
```

### 7. Response Formatting (`app/formatter/response_formatter.py`)

**Main Function:** `format_response(question, sql, results, domain)`

Formats results based on type:

- **Single Value (COUNT/SUM/AVG)** → Natural sentence
  - Input: `[{"count": 42}]`
  - Output: "There are 42 active students in IOI Bengaluru."

- **Multiple Rows** → Table format
  - Headers: Column names
  - Rows: Data
  - Pagination: "Showing 1-50 of 1,234 results"

- **Large Result Sets** → Paginated
  - First 50 rows shown
  - "Show more" option

---

## NL→SQL Pipeline

### Step-by-Step Execution

```
User Question: "How many students have attendance < 75%?"
        ↓
┌───────────────────────────────────────┐
│ Step 1: Domain Classification         │ ← classify_domain()
│ Output: "attendance"                  │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│ Step 2: Build Schema Context          │ ← build_schema_context("attendance")
│ Includes: Student, Attendance, Class, │
│ Center, Batch, Semester, Division     │
│ (10 tables, not 30+)                  │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│ Step 3: Ambiguity Detection           │ ← assess_ambiguity()
│ Is question clear? YES → Continue     │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│ Step 4a: SQL Generation (Attempt 1)   │ ← generate_sql()
│ LLM generates SQL with filters        │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│ Step 5a: SQL Validation (Attempt 1)   │ ← validate_sql()
│ ✓ Single statement                    │
│ ✓ SELECT only                         │
│ ✓ Allowed tables (Student, ...)       │
│ ✓ Business filters present            │
│ ✓ Valid syntax                        │
│ Result: VALID ✓                       │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│ Step 6a: Query Execution (Attempt 1)  │ ← execute_read_query()
│ PostgreSQL runs query                 │
│ Timeout: 30 seconds                   │
│ Max rows: 10,000                      │
│ Result: 156 rows ✓                    │
└───────────────────┬───────────────────┘
                    ↓
┌───────────────────────────────────────┐
│ Step 7: Response Formatting           │ ← format_response()
│ Found 156 students matching criteria  │
│                                       │
│ Name    | Center      | Attendance %  │
│ --------|-------------|---------------│
│ Aadhaar | IOI Noida   | 72.5%         │
│ Rohit   | IOI Delhi   | 68.3%         │
│ ...     | ...         | ...           │
└───────────────────┬───────────────────┘
                    ↓
            User Gets Answer
```

### Retry Logic

If Step 4/5/6 fails, try again (up to 3 times):

```
Attempt 1: Generates SQL → Valid → Executes → 0 Results
  ↓
Feedback: "Query returned 0 results. Your filters may be too strict."
  ↓
Attempt 2: Generates SQL with looser filters → Valid → Executes → 156 Results
  ↓
Return Results
```

---

## Security Model

### Defense in Depth

```
Layer 1: Input Validation
  • Max 500 characters per question
  • No SQL keywords in questions
  ↓
Layer 2: LLM Safety
  • Locked system prompt (immutable)
  • Role definition: "You are a SQL generator"
  • No prompt injection vectors
  ↓
Layer 3: Schema Restriction
  • Only 10 allowed tables
  • No access to sensitive tables
  ↓
Layer 4: Business Filters
  • Automatic filter injection
  • Center exclusions (PW Skills, TEST)
  • Student filters (active, no dummy emails)
  ↓
Layer 5: SQL Validation
  • 7-point validation engine
  • Table whitelist enforcement
  • Filter presence checks
  ↓
Layer 6: Database Level
  • Read-only PostgreSQL role
  • No write permissions
  • Limited connection pool
  ↓
Layer 7: Runtime Protection
  • 30-second query timeout
  • 10,000 row limit
  • Rate limiting (10 req/min)
  ↓
Layer 8: Audit Logging
  • All queries logged
  • Security incidents tracked
  • Review trail maintained
```

### Validation Rules

| Check | Rejects | Allows |
|-------|---------|--------|
| Statement Type | INSERT, UPDATE, DELETE, DROP | SELECT, WITH...SELECT |
| Multiple Statements | `; DROP TABLE...` | Single statement only |
| Forbidden Keywords | GRANT, REVOKE, EXEC, etc | SELECT, WHERE, JOIN, GROUP BY |
| Fake Queries | `SELECT 'answer'` (no FROM) | Real table queries |
| Allowed Tables | problem, submission, contest, Exam, Club, Placement | Student, Teacher, Center, Batch, School, Subject, Semester, Division, Class, Attendance |
| Business Filters | Queries without center/student filters | Queries with mandatory filters |

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 12+ (or SQLite for dev)
- Git

### Local Setup
pip install openai

#### Backend

```bash
# Clone and navigate
git clone https://github.com/UmeshGit125/ChatBot.git
cd ChatBot

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies with uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# Run backend
uv run uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
# Access at http://localhost:3000
```

#### Database

```bash
# For PostgreSQL
psql -U postgres
CREATE DATABASE college_db;
\c college_db
\i db/schema.sql  # If schema file exists

# For SQLite (dev only)
# Automatically created at ./mock.db

# Set in .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/college_db
```

---

## Ambiguity Detection & Clarification

### How It Works

The system automatically detects ambiguous questions and asks for clarification before generating SQL:

1. **First Pass:** Detect vague terms (performance, top, recent, etc.)
2. **Ask User:** Provide clarifying question with suggestions
3. **Second Pass:** If still ambiguous after user response, ask again
4. **Generate SQL:** Once clear, generate the query

### Ambiguous Patterns

**Vague Metrics:**
```
❌ "Show top students" → Ambiguous (by what metric?)
✅ User clarifies: "by attendance percentage"
→ Now clear, generate SQL
```

**Missing Date Range:**
```
❌ "Tell me attendance data" → Ambiguous (which period?)
✅ User clarifies: "last 7 days"
→ Now clear, generate SQL
```

**Composite Identifier Confirmation:**
```
❌ "Show data for 1sot24b1" → Ask confirmation
Question: "Do you mean Center 1, SOT school, Batch 24, Division B1?"
✅ User confirms
→ Now clear, generate SQL
```

### Implementation

The system uses `AMBIGUITY_ASSESSMENT_PROMPT` to:
1. Detect vague terms and missing context
2. Generate targeted clarifying questions
3. Return JSON with clarification request or "is_clear: true"

---

## Identifier Composition Parsing

### Understanding Complex Identifiers

When users provide composite identifiers like "1sot24b1", the system automatically parses:

```
1sot24b1
├─ "1" → Center.code = 1 (IOI Bengaluru)
├─ "sot" → School.name = 'SOT'
├─ "24" → Batch.name = '24'
└─ "b1" → Division.code = 'B1'
```

### Auto-Recognition

The LLM will automatically understand:
- `1sot24b1` → Center(1) + SOT + Batch(24) + Division(B1)
- `3som25a2` → Center(3) + SOM + Batch(25) + Division(A2)
- `2ioi23c1` → Center(2) + IOI + Batch(23) + Division(C1)

### SQL Generation Example

```sql
WHERE c.code = 1
  AND s.name = 'SOT'
  AND b.name = '24'
  AND d.code = 'B1'
  AND s.center_id = c.id  -- Validate relationship
  AND b.school_id = s.id  -- Validate relationship
```

---

## Date-Based Attendance Queries

### Calculate First, Filter Second

**CRITICAL PATTERN:**
```
Step 1: Filter by date range
Step 2: Calculate attendance percentage
Step 3: Apply HAVING clause with percentage filter
```

**Example: Students with <30% attendance in last 7 days**

```sql
WITH attendance_stats AS (
  SELECT
    s.id, s.name,
    COUNT(a.id) as total_classes,
    ROUND(
      COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) * 100.0 /
      NULLIF(COUNT(a.id), 0),
      2
    ) as attendance_pct
  FROM "Student" s
  LEFT JOIN "Attendance" a ON s.id = a.student_id
  LEFT JOIN "Class" cl ON a.class_id = cl.id
  WHERE s.is_active = true
    AND cl.start_date >= CURRENT_DATE - INTERVAL '7 days'
    AND cl.start_date < CURRENT_DATE + INTERVAL '1 day'
  GROUP BY s.id, s.name
)
SELECT * FROM attendance_stats
WHERE attendance_pct < 30
ORDER BY attendance_pct ASC;
```

### Date Range Interpretation

**"Last 7 days":**
```sql
WHERE cl.start_date >= CURRENT_DATE - INTERVAL '7 days'
  AND cl.start_date < CURRENT_DATE + INTERVAL '1 day'
```

**"Last week" (Calendar week Mon-Sun):**
```sql
WHERE EXTRACT(WEEK FROM cl.start_date) = EXTRACT(WEEK FROM CURRENT_DATE - INTERVAL '7 days')
  AND EXTRACT(YEAR FROM cl.start_date) = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '7 days')
```

**"This month":**
```sql
WHERE EXTRACT(MONTH FROM cl.start_date) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM cl.start_date) = EXTRACT(YEAR FROM CURRENT_DATE)
```

**"Between specific dates":**
```sql
WHERE cl.start_date >= 'START_DATE'::timestamp
  AND cl.start_date <= 'END_DATE'::timestamp + INTERVAL '1 day'
```

### Continuously Absent Pattern

**Students continuously absent for a period:**

```sql
WITH absence_records AS (
  SELECT s.id, s.name,
         COUNT(a.id) as absent_count,
         COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) as present_count
  FROM "Student" s
  JOIN "Attendance" a ON s.id = a.student_id
  JOIN "Class" cl ON a.class_id = cl.id
  WHERE s.is_active = true
    AND a.status = 'ABSENT'
    AND cl.start_date >= CURRENT_DATE - INTERVAL '7 days'
  GROUP BY s.id, s.name
)
SELECT * FROM absence_records
WHERE present_count = 0  -- NO present records in range
ORDER BY absent_count DESC;
```

### Weekly Trend Analysis

**Track attendance week-over-week:**

```sql
WITH weekly_stats AS (
  SELECT
    s.id, s.name,
    EXTRACT(WEEK FROM cl.start_date) as week,
    ROUND(
      COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) * 100.0 /
      NULLIF(COUNT(a.id), 0),
      2
    ) as attendance_pct
  FROM "Student" s
  LEFT JOIN "Attendance" a ON s.id = a.student_id
  LEFT JOIN "Class" cl ON a.class_id = cl.id
  WHERE s.is_active = true
    AND cl.start_date >= CURRENT_DATE - INTERVAL '28 days'
  GROUP BY s.id, s.name, week
)
SELECT * FROM weekly_stats
ORDER BY s.id, week;
```

---

## Adding Features

### Adding a New Question Type

**Example:** "Show students with highest attendance"

#### Step 1: Test It Works

```bash
# Ask the question
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Show students with highest attendance"}'

# If it works already - great! The system is flexible.
# If not, proceed to Step 2.
```

#### Step 2: Improve the Prompt

Edit `app/llm/prompts/templates.py`:

```python
# Add example to SQL_GENERATION_PROMPT:
- Top students by attendance:
  SELECT s.name, s.enrollment_id,
         COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) as present_count
  FROM "Student" s
  LEFT JOIN "Attendance" a ON s.id = a.student_id
  WHERE s.is_active = true
    AND s.email NOT LIKE '%dummyemail%'
  GROUP BY s.id, s.name
  ORDER BY present_count DESC
  LIMIT 10
```

#### Step 3: Add Tests

Create `tests/test_new_question_type.py`:

```python
import pytest
from app.core.pipeline import run_pipeline

@pytest.mark.asyncio
async def test_highest_attendance_query():
    question = "Show students with highest attendance"
    result = await run_pipeline(question)
    
    # Verify result
    assert result.sql is not None
    assert "ORDER BY" in result.sql.upper()
    assert "\"Student\"" in result.sql
    assert "\"Attendance\"" in result.sql
    assert result.error is None
```

Run tests:
```bash
uv run pytest tests/test_new_question_type.py -v
```

#### Step 4: Commit

```bash
git add app/llm/prompts/templates.py tests/test_new_question_type.py
git commit -m "Add support for highest attendance query

- Add example query to SQL generation prompt
- Add test case for validation
- Works with existing infrastructure"
```

### Adding a Validation Rule

**Example:** Prevent queries on Mondays (hypothetical)

#### Step 1: Add Validation Function

Edit `app/guardrails/sql_validator.py`:

```python
def _check_no_monday_queries(sql: str) -> ValidationResult:
    """Prevent queries from running on Mondays."""
    import datetime
    if datetime.datetime.now().weekday() == 0:  # Monday
        return ValidationResult(
            is_valid=False,
            error_message="Queries are disabled on Mondays for maintenance."
        )
    return ValidationResult(is_valid=True)

def validate_sql(sql: str, check_business_filters: bool = True) -> ValidationResult:
    # ... existing checks ...
    
    # NEW CHECK
    result = _check_no_monday_queries(sql)
    if not result.is_valid:
        return result
    
    return ValidationResult(is_valid=True, sanitized_sql=sql)
```

#### Step 2: Test It

```bash
# Mock a Monday and test
uv run pytest tests/test_sql_validator.py::test_monday_query_rejection -v
```

---

## Testing

### Test Structure

```
tests/
├── test_domain_classifier.py       # LLM domain classification
├── test_sql_generation.py          # LLM SQL generation
├── test_sql_validator.py           # Validation engine
├── test_business_filters.py        # Filter enforcement
├── test_pipeline.py                # Full pipeline tests
├── test_response_formatter.py      # Output formatting
├── test_database.py                # Database connectivity
├── test_attendance_queries.py      # Attendance-specific
├── test_student_queries.py         # Student-specific
└── test_integration.py             # End-to-end tests
```

### Run Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific file
uv run pytest tests/test_sql_validator.py -v

# Specific test
uv run pytest tests/test_sql_validator.py::test_forbidden_keywords -v

# With coverage
uv run pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html
```

### Write a Test

Example: Test table restriction

```python
# tests/test_sql_validator.py

import pytest
from app.guardrails.sql_validator import validate_sql

def test_reject_problem_table():
    """Ensure problem table (coding platform) is rejected."""
    sql = "SELECT * FROM problem WHERE difficulty = 'EASY'"
    result = validate_sql(sql)
    
    assert result.is_valid == False
    assert "Unauthorized table" in result.error_message
    assert "problem" in result.error_message.lower()

def test_reject_exam_table():
    """Ensure Exam table is rejected."""
    sql = "SELECT * FROM \"Exam\" WHERE full_marks > 50"
    result = validate_sql(sql)
    
    assert result.is_valid == False
    assert "Exam" in result.error_message or "exam" in result.error_message.lower()

def test_allow_student_table():
    """Ensure Student table is allowed."""
    sql = """SELECT name FROM \"Student\" 
             WHERE is_active = true 
             AND email NOT LIKE '%dummyemail%'"""
    result = validate_sql(sql)
    
    assert result.is_valid == True
```

---

## Troubleshooting

### Issue: "Query returned 0 results"

**Causes:**
1. Filters too strict (date range, center name, etc.)
2. Data doesn't exist in expected center
3. All relevant students inactive or using dummy emails
4. Typo in search term

**Solutions:**
1. Check if center exists (not PW Skills or TEST Center)
2. Verify student is active: `is_active = true`
3. Use ILIKE instead of exact match
4. Remove date filters and try again
5. Check logs: `GET /api/logs?limit=10`

### Issue: "Forbidden table detected"

**Cause:** Query references a table outside the 10 allowed ones.

**Solution:** Only use these tables:
```
Teacher, Center, Batch, School, Subject, Semester,
Division, Class, Attendance, Student
```

Cannot use:
```
problem, submission, contest, Exam, StudentExamMarks,
Club, Placement, Project, Certification, Cohort, etc.
```

### Issue: "Missing mandatory filter"

**Cause:** Generated SQL missing required business filters.

**Solution:** System auto-injects filters. If this persists:
1. Check prompt in `templates.py`
2. Verify filter examples are clear
3. Check validator in `sql_validator.py`

### Issue: Database Connection Timeout

**Causes:**
1. PostgreSQL not running
2. Connection string wrong
3. Network unreachable
4. Query too slow (>30s)

**Solutions:**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Verify connection string
echo $DATABASE_URL

# Check logs
tail -f logs/app.log

# Try simpler query first
SELECT COUNT(*) FROM "Student"
```

### Issue: LLM Not Generating Correct SQL

**Causes:**
1. Schema context missing important info
2. Prompt example unclear
3. LLM needs feedback (common issue)

**Solutions:**
1. Check `build_schema_context()` output
2. Add better example to prompt
3. Let retry logic work (up to 3 attempts)
4. Check logs for generated SQL

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No security warnings: Review `Claude/SECURITY.md`
- [ ] Database constraints enforced: Test table restriction
- [ ] Business filters working: Test center/student filtering
- [ ] Performance acceptable: <2 seconds P90
- [ ] Error messages safe: No data leaks
- [ ] Audit logging enabled: Check logs
- [ ] Documentation updated: README + GUIDE
- [ ] Rate limiting configured: 10 req/min
- [ ] Database backup strategy: Define backup schedule

### Docker Deployment

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# Verify
curl http://localhost:8000/health
curl http://localhost:3000/

# View logs
docker compose logs -f app
docker compose logs -f frontend
```

### Kubernetes Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatbot-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: chatbot:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-key
              key: key
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

### Monitoring

```bash
# Key metrics to monitor
- HTTP request latency (should be <2s P90)
- SQL query execution time
- LLM API latency
- Database connection pool usage
- Rate limit violations
- Error rate (should be <1%)
- Security validation failures

# Prometheus metrics
GET /metrics
```

---

## References

For more information, see:

| Document | Contents |
|----------|----------|
| [Claude/DATABASE_RULES.md](../Claude/DATABASE_RULES.md) | 10 tables, business filters, detailed schema |
| [Claude/SECURITY.md](../Claude/SECURITY.md) | Security model, validation rules, incident response |
| [Claude/ARCHITECTURE.md](../Claude/ARCHITECTURE.md) | System design, components, tech stack |
| [Claude/PROMPTS.md](../Claude/PROMPTS.md) | LLM prompt engineering, safety measures |
| [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md) | What was changed and why |
| [README.md](../README.md) | User-facing documentation |

---

**Last Updated:** 2026-08-07 | **Status:** Production Ready | **Maintained by:** Development Team
