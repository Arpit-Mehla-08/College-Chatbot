# Claude Code Session Configuration

This file documents the Claude AI assistant session working on the College NL→SQL Chatbot.

## Session Objectives

This session focuses on:
1. **Improving SQL accuracy** by restricting queries to exactly 10 database tables
2. **Enforcing strict business rules** for data filtering and exclusions
3. **Strengthening security guardrails** with enhanced SQL validation
4. **Enhancing LLM prompts** with better schema context and examples
5. **Completing all documentation** for production deployment

## Key Constraints (MUST Follow)

### Allowed Tables Only
```
Teacher, Center, Batch, School, Subject, Semester, Division, Class, Attendance, Student
```
NO other tables should be used. NO exceptions.

### Data Filtering Rules (ALWAYS Applied)
1. **Exclude "PW Skills" centers**: Filter `WHERE center.name NOT LIKE '%PW Skills%'`
2. **Exclude "TEST Center"**: Filter `WHERE center.name != 'TEST Center'`
3. **Active students only**: Filter `WHERE student.is_active = true`
4. **No dummy emails**: Filter `WHERE student.email NOT LIKE '%dummyemail%'`

These filters must be AUTOMATICALLY applied to every query. They are not optional.

### SQL Generation Rules
- PostgreSQL only
- SELECT queries only - NEVER INSERT/UPDATE/DELETE/DROP/ALTER
- Use proper JOINs based on foreign keys
- Avoid Cartesian joins
- Always use table aliases for readability
- Use aggregation correctly with GROUP BY
- Respect query complexity limits

## Development Flow

### Phase 1: Documentation ✓
- [x] Set up Claude configuration files
- [x] Document architecture clearly
- [x] Define all constraints

### Phase 2: Code Updates ✓
- [x] Update SQL generation prompts
- [x] Update context builder to restrict tables
- [x] Add business rule filters to schema introspection
- [x] Enhance SQL validator
- [x] Update pipeline to enforce constraints

### Phase 3: Testing & Validation
- [ ] Test queries with constraints
- [ ] Verify all filters are applied
- [ ] Test edge cases

### Phase 4: Documentation & Deployment
- [x] Update README.md
- [x] Update GUIDE.md
- [ ] Prepare for production

## Important Files to Modify

**Backend:**
- `app/llm/prompts/templates.py` - SQL generation prompts ✓
- `app/schema/context_builder.py` - Schema filtering ✓
- `app/schema/annotations.yaml` - Table definitions ✓
- `app/guardrails/sql_validator.py` - SQL validation ✓
- `app/core/pipeline.py` - Pipeline orchestration

**Documentation:**
- `Claude/DATABASE_RULES.md` - Filtering rules detail ✓
- `Claude/PROMPTS.md` - Prompt engineering ✓
- `docs/GUIDE.md` - Developer guide ✓
- `README.md` - Project overview ✓

## Performance Goals

- Response time: < 2 seconds for 90% of queries
- Token efficiency: Optimize LLM prompts to reduce token usage
- Accuracy: 95%+ for queries in the 10-table scope
- Security: 100% - no unsafe queries ever reach the database

## Notes for Next Session

If this session is interrupted:
1. Check `Claude/SECURITY.md` for current validation rules
2. Review `Claude/DATABASE_RULES.md` for filter requirements
3. See `Claude/PROMPTS.md` for prompt templates
4. Refer to git history for recent changes

## Related Documentation
- See `Claude/ARCHITECTURE.md` for system design
- See `Claude/DATABASE_RULES.md` for detailed filtering
- See `Claude/SECURITY.md` for guardrails
- See `Claude/PROMPTS.md` for LLM configuration
