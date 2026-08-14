# Operational Rules

These are the rules that MUST be followed when working on this project.

## Code Changes

### Rule 1: Never Weaken Security Constraints

**What this means:**
- ❌ Do NOT remove forbidden keywords from sql_validator.py
- ❌ Do NOT remove business filter checks
- ❌ Do NOT allow INSERT/UPDATE/DELETE/DROP statements
- ❌ Do NOT remove table restrictions

**What to do instead:**
- ✅ ADD more security checks
- ✅ IMPROVE error messages
- ✅ ENHANCE validation logic
- ✅ ADD new constraint types

**Why:** Security is non-negotiable. Once removed, it's hard to restore.

### Rule 2: Respect the 10 Table Scope

**These 10 tables ONLY:**
```
Teacher, Center, Batch, School, Subject, Semester, Division, Class, Attendance, Student
```

**Never:**
- ❌ Add queries using other tables (problem, submission, contest, etc.)
- ❌ Remove these tables from allowed list
- ❌ Create exceptions for "just this one table"

**If you need more tables:**
- 📝 Document the requirement in Github issue
- 🤔 Discuss scope expansion (Phase 2)
- ✅ Only after approval, update constraints everywhere

### Rule 3: Always Apply Business Filters

**Every query must filter:**
```sql
-- If Student table:
WHERE student.is_active = true
  AND student.email NOT LIKE '%dummyemail%'

-- If Center table:
WHERE center.name NOT LIKE '%PW Skills%'
  AND center.name != 'TEST Center'
```

**Never:**
- ❌ Generate queries without these filters
- ❌ Create "admin" mode that skips filters
- ❌ Say "filters are optional"

**Why:** These aren't preferences - they're business rules.

### Rule 4: Test Everything You Change

**Before committing:**
```bash
# Run all tests
uv run pytest tests/ -v

# Check specific domain
uv run pytest tests/test_sql_validator.py -v

# Test with real questions
uv run pytest tests/test_integration.py -v
```

**Never:**
- ❌ Commit code without running tests
- ❌ Say "the tests are optional"
- ❌ Break existing tests without updating them

### Rule 5: Document What You Change

**Git commits must include:**
```
Subject: Brief description of change

Body:
- What changed: "Updated SQL generation prompt"
- Why changed: "To enforce 10-table scope"
- How tested: "Ran 15 test cases, all pass"
- Related: "See Claude/DATABASE_RULES.md"
```

**Never:**
- ❌ Commit with vague messages ("fixed stuff")
- ❌ Forget to mention constraint changes
- ❌ Say "will document later"

### Rule 6: No Backward Compatibility Hacks

**If something needs to change, change it properly:**

```python
# ❌ BAD: Add a flag for old behavior
if os.getenv("LEGACY_MODE"):
    # old code
else:
    # new code

# ✓ GOOD: Just use new behavior everywhere
# new code only
```

**Why:** Hacks become technical debt and create security holes.

## Documentation

### Rule 7: Keep Claude Files Updated

**When you change code, update docs:**

| Code Change | Update This |
|-------------|-------------|
| Add constraint | SECURITY.md, DATABASE_RULES.md |
| Change prompt | PROMPTS.md |
| Change architecture | ARCHITECTURE.md |
| Change business rules | DATABASE_RULES.md, RULES.md |
| Update tables | DATABASE_RULES.md, CONTEXT.md |

**Never:**
- ❌ Make code changes without updating docs
- ❌ Say "code is self-documenting"
- ❌ Leave TODOs in docs

### Rule 8: README and GUIDE Must Be Clear

**They should explain:**
- ✅ What the system does
- ✅ How to run it
- ✅ What constraints apply
- ✅ How to deploy it
- ✅ How to extend it

**Never:**
- ❌ Leave placeholders like "[TODO]"
- ❌ Use jargon without explanation
- ❌ Assume reader knows the context

## Git Workflow

### Rule 9: Branch Naming

**Use meaningful names:**
```
feature/table-restriction
fix/sql-validation
security/enforce-filters
docs/update-database-rules
```

**Never:**
- ❌ My branch name: "fix-stuff"
- ❌ Random numbers: "feature-123456"
- ❌ Personal names: "arpit-changes"

### Rule 10: Commit Frequency

**Commit often:**
- One logical change per commit
- Atomic commits (self-contained)
- Small enough to review easily

**Examples:**
```
Commit 1: Add table whitelist to schema context
Commit 2: Update SQL generation prompt with constraints
Commit 3: Add business filter validation to validator
Commit 4: Update documentation
```

**Never:**
- ❌ Huge commits with 10 unrelated changes
- ❌ Half-complete features
- ❌ Broken intermediate commits

### Rule 11: PR Description

**Include:**
```markdown
## What
Rename "tables" to "allowed_tables" for clarity

## Why
Making it explicit that only these 10 tables are permitted

## Testing
- [ ] Manual: Tested with attendance query
- [ ] Manual: Tested with invalid table reference
- [ ] Automated: 80 tests pass
- [ ] New: Added 5 tests for table validation

## Security Impact
- Enforces table restriction (✓)
- Improves clarity (✓)
- No breaking changes (✓)

## Checklist
- [ ] Code reviewed
- [ ] Tests pass
- [ ] Docs updated
- [ ] No console errors
```

## Security Review

### Rule 12: Security is Everyone's Responsibility

**Before merging ANY code:**
1. ✅ Does it maintain security constraints?
2. ✅ Could it be exploited?
3. ✅ Does it validate input properly?
4. ✅ Could it bypass filters?
5. ✅ Is error handling safe (no data leaks)?

**If ANY answer is "no", DO NOT MERGE.**

### Rule 13: Report Vulnerabilities Immediately

**If you find a security issue:**
1. 🛑 STOP what you're doing
2. 📝 Document the issue
3. 🚨 Report to team immediately
4. 🔒 Create PR to fix (in security branch)
5. 🔍 Do NOT merge until reviewed

**Example of reportable issues:**
- SQL injection vector
- Unauthorized table access
- Business filter bypass
- Rate limiting bypass
- Error message information leak

## Quality Standards

### Rule 14: Code Quality

**Must pass:**
- ✅ Linting (flake8)
- ✅ Type checking (mypy)
- ✅ Test coverage (>80%)
- ✅ No TODO comments in merged code

**How to check locally:**
```bash
# Linting
uv run flake8 app/ --max-line-length=100

# Type checking
uv run mypy app/

# Test coverage
uv run pytest tests/ --cov=app --cov-report=term-missing
```

### Rule 15: Naming Conventions

**Variables and functions:**
```python
# ✓ GOOD: Clear, descriptive
allowed_tables = ["Teacher", "Center", ...]
validate_business_filters(sql: str) -> bool:

# ❌ BAD: Unclear
a = [...]
chk(s):
```

**Classes and constants:**
```python
# ✓ GOOD
class SQLValidator:
MAX_QUERY_LENGTH = 2000
FORBIDDEN_KEYWORDS = {...}

# ❌ BAD
class validator:
max_len = 2000
keywords = {...}
```

## Performance Standards

### Rule 16: Response Time Budget

**Total: <2 seconds (P90)**
- Domain classification: <200ms
- Schema context: <100ms
- LLM generation: <1000ms
- SQL validation: <50ms
- Query execution: <500ms
- Response formatting: <100ms

**If a component takes longer:**
- 📊 Profile it (measure where time goes)
- 🔍 Optimize hotspots
- 📝 Document why (if justified)

### Rule 17: Memory Usage

**Per request: <100MB**
**Per session: <200MB**

If exceeding:
- 🔍 Check for memory leaks
- 📊 Profile memory usage
- ✅ Optimize or add caching

## Escalation Path

### I Have a Question → Who Do I Ask?

**Architecture question?**
→ Read Claude/ARCHITECTURE.md → Ask in PR

**Database/filtering question?**
→ Read Claude/DATABASE_RULES.md → Ask in PR

**Security concern?**
→ Read Claude/SECURITY.md → DM immediately

**Prompt engineering question?**
→ Read Claude/PROMPTS.md → Discuss in PR

**Deployment question?**
→ Read docs/DEPLOYMENT.md → Ask in PR

## Checklists

### Before You Start Coding
- [ ] Read relevant Claude/*.md files
- [ ] Check existing tests (don't duplicate)
- [ ] Understand the constraints
- [ ] Plan your changes (write them down)

### Before You Commit
- [ ] Run: `uv run pytest tests/ -v`
- [ ] Run: `uv run flake8 app/`
- [ ] Check: No TODO comments
- [ ] Check: No debug print statements
- [ ] Write: Clear commit message
- [ ] Update: Relevant documentation

### Before You Open PR
- [ ] Verify: Tests pass (run locally)
- [ ] Verify: No broken functionality
- [ ] Check: No security regression
- [ ] Read: Your own diff (catch mistakes)
- [ ] Write: Clear PR description
- [ ] Request: Reviews from team

### Before PR Can Be Merged
- [ ] At least 1 code review approval
- [ ] All tests pass (CI/CD)
- [ ] Security review passed
- [ ] Documentation updated
- [ ] No conflicts with main branch

## When Something Goes Wrong

### Production Bug Found
1. 🚨 Alert team immediately
2. 🔍 Identify root cause
3. 🛠️ Fix in dedicated branch
4. ✅ Test thoroughly locally
5. 🔄 Get quick code review
6. ⚡ Merge and deploy
7. 📝 Document incident
8. 🔐 Add tests to prevent recurrence

### Test Suite Failure
1. 🔍 Identify failing test
2. 🐛 Understand what it's testing
3. 🛠️ Fix your code or the test
4. ✅ Verify fix works
5. 🚫 Never skip/disable tests

### Security Concern
1. 🛑 DO NOT MERGE ANYTHING
2. 🚨 Report to team immediately
3. 🔍 Investigate thoroughly
4. 📝 Document the issue
5. 🛠️ Implement fix
6. ✅ Get security review
7. ⚡ Deploy fix

## Final Notes

**These rules exist because:**
- ✅ Security is more important than speed
- ✅ Documentation helps future developers
- ✅ Tests catch bugs early
- ✅ Code review improves quality
- ✅ Clear communication prevents misunderstandings

**If you break a rule:**
- 🤝 Discuss with team why
- 📝 Document the exception
- 🔄 Update the rule if needed
- ✅ Never ignore the rule silently

**Remember:** The goal is a safe, accurate, maintainable system for years to come.
