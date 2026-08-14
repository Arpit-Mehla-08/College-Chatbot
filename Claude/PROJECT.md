# Project Overview

## What is This?

College NL→SQL Chatbot - A production-grade system that converts natural language questions into accurate PostgreSQL queries against a college operations database.

**In Plain English:**
- User asks: "How many active students are in IOI Bengaluru?"
- System converts to SQL: `SELECT COUNT(*) FROM "Student" WHERE is_active = true AND center_id = ...`
- Database executes
- System returns: "There are 234 active students in IOI Bengaluru."

**No SQL knowledge needed.**

## Why This Project?

**Problem:** College administrators spend hours writing SQL queries to answer simple operational questions.

**Solution:** Chat with an AI that understands:
- Natural language (English, Hindi, Hinglish)
- College operations (attendance, academics, etc.)
- Database schema (relationships, constraints, data types)
- Business rules (exclude test centers, dummy accounts, etc.)

**Result:** Instant answers to operational questions.

## Key Success Criteria

1. **Accuracy:** 95%+ of queries are correct (in scope)
2. **Safety:** 100% - no unsafe queries ever reach the database
3. **Speed:** <2 seconds response time for 90% of queries
4. **Scope:** Only 10 tables, 4 mandatory business filters
5. **Usability:** Works for any language (EN/HI/Hinglish)

## Technical Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| Backend | FastAPI | Fast, async, great for LLM calls |
| LLM | Google Gemini | Accurate, cheap, fast for SQL generation |
| Database | PostgreSQL | Robust, great for analytics queries |
| Frontend | Next.js | Responsive, great chat UI |
| Deployment | Docker | Consistent across environments |

## The 10 Allowed Tables

1. **Teacher** - Faculty members and instructors
2. **Center** - Physical campus locations
3. **Batch** - Student cohorts (Batch 23, 24, etc.)
4. **School** - Schools/programs within centers (SOT, SOM, etc.)
5. **Subject** - Academic subjects/courses
6. **Semester** - Academic periods (1st sem, 2nd sem, etc.)
7. **Division** - Sub-groups within batches (A, B, C)
8. **Class** - Scheduled class/lecture sessions
9. **Attendance** - Student attendance records (present/absent/late)
10. **Student** - Student information and enrollment

**Why Only 10?**
- Scope: All questions can be answered using these tables
- Safety: Limits query surface area
- Focus: Ensures high accuracy in this domain
- Future: Can expand to more tables in Phase 2

## Business Rules (ALWAYS Applied)

### Rule 1: Exclude "PW Skills" Centers
```sql
WHERE center.name NOT LIKE '%PW Skills%'
```
**Why:** These are franchise/partner centers managed separately

### Rule 2: Exclude "TEST Center"
```sql
WHERE center.name != 'TEST Center'
```
**Why:** This is a development/testing center

### Rule 3: Active Students Only
```sql
WHERE student.is_active = true
```
**Why:** Graduated/dropped students shouldn't appear in current reports

### Rule 4: No Dummy Emails
```sql
WHERE student.email NOT LIKE '%dummyemail%'
```
**Why:** Test accounts should never appear in production reports

**These rules are MANDATORY. No exception. Ever.**

## Current Status

### Completed ✓
- FastAPI backend with core endpoints
- Gemini LLM integration with retry logic
- SQL validation with security guardrails
- Schema introspection from database
- Response formatting (tables, natural language)
- Multi-language support (EN/HI/Hinglish)
- Docker containerization
- 80+ test cases
- Basic documentation

### In This Session ✓
- Strict table restriction (only 10 allowed)
- Business filter enforcement (center exclusions, active students, etc.)
- Enhanced prompt engineering (better SQL generation)
- Complete documentation (Claude session files)
- Security hardening (validation improvements)
- Complete README.md and docs/GUIDE.md rewrite

### TODO (Phase 2)
- Advanced chart generation
- Query caching/optimization
- Multi-user session management
- Analytics dashboard
- Performance monitoring

## Deployment Options

### Option 1: Render + Vercel (Recommended)
- Backend: Render.com (Docker web service)
- Frontend: Vercel.com (serverless)
- Database: PostgreSQL on AWS RDS
- CDN: Vercel edge network

### Option 2: AWS
- Backend: EC2 or Fargate (Docker)
- Frontend: CloudFront + S3
- Database: RDS PostgreSQL
- Cache: ElastiCache (Redis)

### Option 3: On-Premise
- Backend: Your server (Docker)
- Frontend: Your server (Nginx)
- Database: Local PostgreSQL
- Monitoring: Prometheus + Grafana

## Development Workflow

### Local Development
```bash
# Terminal 1: Backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Tests
uv run pytest tests/ -v
```

### Docker Development
```bash
docker compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## Long-Term Vision

**Phase 1 (Current):** College operations queries (10 tables)

**Phase 2:** Expand to full schema (30+ tables)

**Phase 3:** Multi-company support (different databases)

**Phase 4:** Custom LLM fine-tuning (faster, cheaper)

**Phase 5:** Advanced features (charts, exports, saved queries)

**Phase 6:** Mobile app, browser extensions, integrations
