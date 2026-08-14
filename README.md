# College NL→SQL Chatbot

A production-grade natural language to SQL chatbot that lets you query a college database using plain English, Hindi, or Hinglish. Ask questions in your language, get instant answers. No SQL knowledge needed.

**Status:** Production-Ready | **Phase:** 1 (10 Tables) | **Last Updated:** 2026-08-07

---

## What This Does

Converts natural language questions into accurate PostgreSQL queries against a college operations database:

- **User Question:** "How many active students are in IOI Bengaluru?"
- **System converts to SQL:** Generates accurate query with business filters
- **Database executes:** Runs safely (SELECT only)
- **Returns answer:** "There are 234 active students in IOI Bengaluru."

### Supported Domains

- ✅ **Attendance** - Student presence, absence, attendance reports
- ✅ **Students** - Student info, enrollment, demographics
- ✅ **Academics** - Subjects, semesters, classes, teachers
- ✅ **General** - Cross-domain queries on college data

### Example Queries

| Question | Result |
|----------|--------|
| "How many students have attendance below 75%?" | Returns students ranked by attendance |
| "List students in Batch 24, IOI Noida" | Filters by batch and center |
| "Who is teaching Web Development?" | Returns teacher information |
| "How many classes did we have in the last week?" | Counts classes in date range |
| "किस छात्र की उपस्थिति सबसे कम है?" (Hindi) | Works in any language |

---

## Key Features

### 🎯 Accurate
- Scoped to **10 specific tables** (no hallucination of extra tables)
- **4 mandatory business filters** enforced automatically
- Multi-layer SQL validation (7 checks)
- Retry logic with feedback (up to 3 attempts)

### 🔒 Secure
- SELECT queries ONLY (no INSERT/UPDATE/DELETE/DROP/ALTER)
- Automatic filter enforcement:
  - Excludes "PW Skills" centers
  - Excludes "TEST Center"
  - Includes active students only
  - Filters out dummy email accounts
- Read-only database role
- 30-second query timeout
- Rate limiting (10 req/min per session)

### 🚀 Fast
- <2 seconds response time (P90)
- Async database queries
- Schema context caching
- Optimized LLM prompts

### 🌐 Multilingual
- English, Hindi, Hinglish input
- Automatically detects language
- Returns response in same language

### 📊 Well Documented
- 8 comprehensive documentation files
- Architecture diagrams
- Schema reference
- Security model
- Operational rules

---

## System Architecture

```
User Question (EN/HI/Hinglish)
         │
         ▼
┌─────────────────────────────┐
│  Domain Classification       │ → Attendance / Students / Academics / General
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Build Schema Context        │ → Only 10 allowed tables
│  ├─ Table definitions        │ → Column descriptions  
│  ├─ Relationships            │ → FK paths
│  └─ Sample data values       │ → For LLM grounding
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  SQL Generation (Gemini LLM) │ → PostgreSQL with filters
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  SQL Validation             │ ✓ Single statement only
│  ├─ No DML/DDL             │ ✓ SELECT only
│  ├─ Allowed tables only     │ ✓ No unauthorized tables
│  ├─ Business filters        │ ✓ Required filters present
│  └─ Syntax check            │ ✓ Valid PostgreSQL
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Query Execution (PostgreSQL) │ → Read-only connection
│  ├─ Timeout: 30s            │    Max rows: 10,000
│  └─ Async driver            │    Connection pooling
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Response Formatting        │ → Natural language + Table
│  ├─ Single value → Sentence │ → "There are 42 students"
│  ├─ Multiple rows → Table   │ → Formatted results
│  └─ Charts (optional)       │ → Visual representation
└──────────┬──────────────────┘
           │
           ▼
    User Gets Answer
```

---

## Database Scope (Phase 1)

### ✅ Allowed Tables (EXACTLY 10)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| **Student** | Learners enrolled | name, email, is_active, center_id, enrollment_id |
| **Teacher** | Faculty & instructors | name, email, role, center_id, is_active |
| **Center** | Campus locations | name, location, code |
| **Batch** | Student cohorts (Batch 23, 24, etc.) | name, center_id, school_id |
| **School** | Schools/programs (SOT, SOM) | name, center_id |
| **Division** | Batch sub-groups (A, B, C) | code, batch_id, center_id |
| **Semester** | Academic periods (1st, 2nd, 3rd sem) | number, division_id, start_date, end_date |
| **Subject** | Courses taught | name, code, semester_id, teacher_id |
| **Class** | Scheduled lectures | subject_id, teacher_id, division_id, start_date |
| **Attendance** | Student presence records | student_id, class_id, status (PRESENT/ABSENT/LATE) |

**NO other tables are accessible.** Attempting to use other tables (problem, submission, contest, Exam, StudentExamMarks, Club, Placement, Project, Certification, etc.) will result in an error.

### 🔐 Mandatory Business Filters (ALWAYS APPLIED)

These filters are **automatically enforced** on every query:

#### 1. Exclude "PW Skills" Centers
```sql
WHERE center.name NOT LIKE '%PW Skills%'
```
**Excludes:** PW Skills Bangalore, PW Skills Noida, PW Skills Lucknow, etc.

#### 2. Exclude "TEST Center"
```sql
WHERE center.name != 'TEST Center'
```
**Excludes:** Development/testing center

#### 3. Active Students Only
```sql
WHERE student.is_active = true
```
**Includes:** Only currently enrolled students

#### 4. Exclude Dummy Emails
```sql
WHERE student.email NOT LIKE '%dummyemail%'
```
**Excludes:** Test accounts with dummy email addresses

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **Google Gemini API key** ([Get one free](https://aistudio.google.com/apikey))
- **PostgreSQL 12+** (production) or **SQLite** (development)

### Option 1: Docker (Recommended, Easiest)

No Python or Node.js installation needed:

```bash
# Clone and navigate
git clone https://github.com/UmeshGit125/ChatBot.git
cd ChatBot

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start all services (backend + frontend + database)
docker compose up --build

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

Stop with: `docker compose down`

### Option 2: Local Development

#### Step 1: Backend Setup

Using **uv** (fastest):
```bash
# Install uv if needed
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup and run
uv sync
cp .env.example .env
# Edit .env and add GEMINI_API_KEY
uv run uvicorn app.main:app --reload --port 8000
```

Using **pip**:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

#### Step 2: Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Access at http://localhost:3000
```

#### Step 3: Run Tests

```bash
# Backend tests
uv run pytest tests/ -v

# Watch mode
uv run pytest tests/ -v --watch
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Google Gemini API key from [aistudio.google.com](https://aistudio.google.com/apikey) |
| `DATABASE_URL` | `sqlite+aiosqlite:///./mock.db` | Database connection string |
| `LLM_PROVIDER` | `gemini` | LLM provider (`gemini` only currently) |
| `WEEK_DEFINITION` | `calendar` | `calendar` (Mon-Sun) or `rolling7` days |
| `RATE_LIMIT_PER_MINUTE` | `10` | Max requests per session per minute |

### PostgreSQL Connection (Production)

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/college_db
```

Create a read-only role for security:
```sql
CREATE ROLE chatbot_reader WITH LOGIN PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO chatbot_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO chatbot_reader;
```

---

## API Endpoints

### POST /api/chat
**Query the database with natural language**

Request:
```json
{
  "question": "How many students in IOI Delhi?",
  "conversation_id": "optional-uuid-for-context"
}
```

Response:
```json
{
  "answer": "There are 156 active students in IOI Delhi.",
  "sql": "SELECT COUNT(*) FROM \"Student\" WHERE ...",
  "domain": "students",
  "row_count": 1,
  "execution_time_ms": 245
}
```

### GET /api/conversations
**Get conversation history**

Response:
```json
{
  "conversations": [
    {
      "id": "uuid",
      "created_at": "2026-08-07T10:30:00Z",
      "questions": ["How many students?", "In which centers?"]
    }
  ]
}
```

### GET /api/logs?limit=50
**Get query audit logs for debugging**

### GET /health
**Health check**

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "llm_provider": "gemini"
}
```

---

## Project Structure

```
Chat-Bot-Metabase/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── api/
│   │   ├── chat.py             # POST /api/chat endpoint
│   │   ├── conversations.py    # Conversation routes
│   │   └── logs.py             # Audit log routes
│   ├── llm/
│   │   ├── gemini_provider.py  # Gemini integration
│   │   ├── base.py             # Abstract LLM interface
│   │   └── prompts/templates.py # SQL generation prompts
│   ├── db/
│   │   └── connection.py       # PostgreSQL async connection
│   ├── schema/
│   │   ├── context_builder.py  # Schema → LLM context
│   │   ├── introspector.py     # Live schema reader
│   │   └── annotations.yaml    # Table metadata (10 tables only)
│   ├── guardrails/
│   │   └── sql_validator.py    # SQL validation (7 checks)
│   ├── formatter/
│   │   └── response_formatter.py # Format results
│   └── core/
│       ├── pipeline.py         # Main orchestration (NL→SQL)
│       ├── models.py           # Request/response schemas
│       ├── conversation.py     # State management
│       ├── logger.py           # Audit logging
│       └── rate_limiter.py     # Rate limiting
├── frontend/                   # Next.js chat interface
├── tests/                      # 80+ pytest test cases
├── Claude/                     # Session documentation
│   ├── CLAUDE.md               # Session config
│   ├── DATABASE_RULES.md       # Detailed constraints
│   ├── SECURITY.md             # Security model
│   ├── ARCHITECTURE.md         # System design
│   ├── PROMPTS.md              # Prompt engineering
│   ├── PROJECT.md              # Project overview
│   ├── RULES.md                # Operational rules
│   └── CONTEXT.md              # DB reference
├── docs/
│   ├── GUIDE.md                # Developer guide
│   └── DEPLOYMENT.md           # Deployment steps
├── docker-compose.yml          # Multi-container setup
├── Dockerfile                  # Backend container
├── Dockerfile.frontend         # Frontend container
└── README.md                   # This file
```

---

## Security

### Security Model

The system implements **defense in depth** with multiple layers:

1. **Input Validation** - Max 500 chars, no SQL keywords in questions
2. **LLM Safety** - Locked system prompt, role definition
3. **SQL Validator** - 7 checks (single statement, SELECT only, allowed tables, business filters)
4. **Database Role** - Read-only `chatbot_reader` role
5. **Connection Timeout** - 30-second query timeout
6. **Rate Limiting** - 10 requests per minute per session
7. **Audit Logging** - All queries logged for security review
8. **Error Handling** - No data leaks in error messages

### What Can't Be Done

❌ **Completely Blocked:**
- INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
- CREATE, GRANT, REVOKE
- Access to non-10 tables
- Queries without business filters

✅ **Always Happens:**
- Center exclusions (PW Skills, TEST Center)
- Active student filter
- Dummy email filter
- Read-only execution

### Automatic Business Filters

All queries include:
```sql
WHERE student.is_active = true
  AND student.email NOT LIKE '%dummyemail%'
  AND center.name NOT LIKE '%PW Skills%'
  AND center.name != 'TEST Center'
```

---

## Performance

### Response Time Budget

| Component | Time | Total |
|-----------|------|-------|
| Domain classification | 200ms | |
| Schema context building | 100ms | |
| SQL generation (LLM) | 1000ms | |
| SQL validation | 50ms | |
| Query execution | 500ms | |
| Response formatting | 100ms | |
| **Total (P90)** | | **<2 seconds** |

### Throughput

- **Rate limit:** 10 requests/minute per session
- **Connection pool:** 5 connections
- **Max rows per query:** 10,000
- **Query timeout:** 30 seconds
- **Max SQL length:** 2,000 characters

---

## Deployment

### Render + Vercel (Recommended)

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for step-by-step guide.

```yaml
# Backend: Render.com Docker web service
# Frontend: Vercel.com serverless
# Database: AWS RDS PostgreSQL
# Cache: Optional Redis
```

### Docker Compose (Local/Server)

All-in-one local deployment:
```bash
docker compose up --build
```

---

## Testing

### Run Test Suite

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_sql_validator.py -v

# With coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Test Coverage

- ✅ 80+ test cases
- ✅ SQL validator (injection attempts, fake queries)
- ✅ Domain classification (all 9 domains)
- ✅ Business filter enforcement
- ✅ Attendance calculations
- ✅ Join correctness
- ✅ Response formatting

---

## Documentation

For detailed information, see:

| Document | Contents |
|----------|----------|
| [`docs/GUIDE.md`](docs/GUIDE.md) | Complete developer guide, architecture, setup |
| [`Claude/DATABASE_RULES.md`](Claude/DATABASE_RULES.md) | 10 tables, business filters, constraints |
| [`Claude/SECURITY.md`](Claude/SECURITY.md) | Security model, validation rules, incident response |
| [`Claude/ARCHITECTURE.md`](Claude/ARCHITECTURE.md) | System components, data flow, tech stack |
| [`Claude/PROMPTS.md`](Claude/PROMPTS.md) | LLM prompt engineering, safety measures |
| [`Claude/PROJECT.md`](Claude/PROJECT.md) | Project overview, metrics, roadmap |
| [`Claude/RULES.md`](Claude/RULES.md) | Operational rules, git workflow, checklists |
| [`Claude/CONTEXT.md`](Claude/CONTEXT.md) | Database schema reference, query patterns |

---

## Troubleshooting

### "Query returned 0 results"
- Try removing date filters
- Use ILIKE instead of exact matching
- Check if data exists in that center (not PW Skills or TEST)
- Verify student is active (is_active = true)

### "Forbidden table detected"
- Only use these 10 tables: Teacher, Center, Batch, School, Subject, Semester, Division, Class, Attendance, Student
- Cannot query: problem, submission, contest, Exam, StudentExamMarks, Club, Placement, Project, Certification

### "Missing mandatory filter"
- Queries must include automatic filters
- Student queries: `is_active = true AND email NOT LIKE '%dummyemail%'`
- Center queries: `name NOT LIKE '%PW Skills%' AND name != 'TEST Center'`

### "Connection timeout"
- Query exceeded 30-second timeout
- Try filtering by date range
- Reduce complexity (fewer JOINs)
- Check database is responsive

---

## Support & Contributing

### Report Issues

Found a bug? Create an issue on GitHub with:
- Question that triggered it
- Generated SQL
- Expected vs actual result
- Database environment

### Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes following [Claude/RULES.md](Claude/RULES.md)
4. Add tests for new functionality
5. Ensure all tests pass: `pytest tests/ -v`
6. Submit pull request

### Code Quality Standards

- ✅ All tests pass (80+ test cases)
- ✅ Linting passes (flake8)
- ✅ Type checking passes (mypy)
- ✅ >80% code coverage
- ✅ Documentation updated

---

## License

MIT License - See LICENSE file for details

---

## Change Log

### v1.0.0 (2026-08-07)
- ✅ Production-ready NL→SQL chatbot
- ✅ 10-table scope with strict enforcement
- ✅ 4 mandatory business filters
- ✅ 7-layer SQL validation
- ✅ Multi-language support (EN/HI/Hinglish)
- ✅ Comprehensive documentation
- ✅ 80+ test cases
- ✅ Docker containerization
- ✅ Retry logic with feedback
- ✅ Audit logging

### Roadmap

- 📋 Phase 2: Expand to 20+ tables
- 📋 Phase 3: Add chart generation
- 📋 Phase 4: Query caching & optimization
- 📋 Phase 5: Saved queries feature
- 📋 Phase 6: Multi-user support

---

**Last Updated:** 2026-08-07 | **Status:** Production Ready | **Maintained by:** Development Team
