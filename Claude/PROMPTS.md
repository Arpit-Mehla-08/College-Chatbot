# LLM Prompt Engineering Guide

This document explains how prompts are engineered for optimal SQL generation and safety.

## Prompt Philosophy

**Goal:** Generate accurate, safe PostgreSQL queries by giving the LLM:
1. Clear role definition
2. Explicit constraints
3. Real schema context
4. Example patterns
5. Business filter rules

**Anti-Goal:**
- Hallucinated data
- Unsafe operations
- Unrelated tables
- Missing business filters

## Domain Classification Prompt

**File:** app/llm/prompts/templates.py::DOMAIN_CLASSIFICATION_PROMPT

**Purpose:** Route user question to correct domain

**Key Elements:**
1. **Role:** "You are a domain classifier"
2. **Domain List:** Exhaustive list of 9 domains + out_of_scope
3. **Clear Examples:** What IS and ISN'T each domain
4. **Single Output:** Domain name only (one word, lowercase)
5. **Protection:** Explicit "coding domain is NOT for code generation" rule

**Example Prompts → Expected Output:**
```
Q: "How many students in Delhi center?" → students
Q: "What was my attendance last week?" → attendance
Q: "Write a Python function to sort a list" → out_of_scope
Q: "Who got placed with salary >10 LPA?" → placements
Q: "List clubs in IOI Bangalore" → clubs
```

**Why This Works:**
- Single word output: Easy to parse, no ambiguity
- Real examples: LLM learns from concrete cases
- Clear out_of_scope: Prevents attempting to answer unrelated Qs
- Explicit "NOT" rules: Prevents misunderstanding

## Ambiguity Detection & Clarification Prompt

**Purpose:** Detect when user questions are ambiguous and ask for clarification

**Key Elements:**

1. **Identify Ambiguous Phrases:**
   - Vague terms: "performance", "top", "good", "bad" (without context)
   - Missing specifics: Date range not specified, metric not clear
   - Multiple interpretations: "attendance" could mean count or percentage

2. **Ask Clarifying Questions:**
   ```
   First time: "You mentioned 'top students'. Do you mean by attendance percentage,
   exam marks, or number of classes attended?"
   
   Second time: "For 'last week', do you mean the last 7 calendar days or the last
   complete week (Mon-Sun)?"
   
   Third time: "When you say 'batch 24', do you mean Batch 24 in a specific center,
   or all Batch 24 across all centers?"
   ```

3. **Don't Over-Ask:**
   - Only ask if genuinely ambiguous
   - Clear questions should get direct answers
   - Remember context from conversation history

---

## Identifier Composition Guide

**Pattern Recognition for Complex Identifiers:**

When users provide composite identifiers like "1sot24b1", break them down:

```
Identifier: 1sot24b1
├─ "1" → Center code from Center.code = 1 (IOI Bengaluru)
├─ "sot" → School name from School.name = 'SOT' (School of Technology)
├─ "24" → Batch name from Batch.name = '24' (Batch 24)
└─ "b1" → Division code from Division.code = 'B1'

This refers to: Batch 24, School of Technology, IOI Bengaluru, Division B1
```

**How to Handle in SQL:**
```sql
WHERE c.code = 1
  AND s.name = 'SOT'
  AND b.name = '24'
  AND d.code = 'B1'
```

---

## SQL Generation Prompt

**File:** app/llm/prompts/templates.py::SQL_GENERATION_PROMPT

**Purpose:** Generate accurate PostgreSQL SELECT statements

**Key Elements:**

### 1. Role Definition
```
"You are an expert SQL query generator for a PostgreSQL college database."
```

### 2. Hard Constraints
```
RULES:
1. Generate ONLY a single SELECT statement.
2. No INSERT, UPDATE, DELETE, DROP, or any other DML/DDL.
3. Do NOT include semicolons at the end.
4. NEVER generate fake queries like SELECT 'some text message' AS column.
5. Only query real tables with real columns.
```

**Why These Matter:**
- Rule 1: Single statement prevents statement stacking attacks
- Rule 2: Explicitly forbids all dangerous operations
- Rule 3: Prevents SQL injection via semicolon
- Rule 4: Prevents hallucinated data (SELECT 'answer' AS response)
- Rule 5: Forces grounding in actual schema

### 3. Syntax Rules
```
6. Use proper JOINs based on the relationships provided.
7. The question may be in English, Hindi, or Hinglish - always generate standard SQL.
8. Use aliases for readability.
9. For percentage calculations, use CAST or multiply by 100.0 for float division.
10. IMPORTANT: All table names with uppercase letters MUST be double-quoted:
    "Student", "Center", "Batch", "Attendance", etc.
    Lowercase tables like problem, submission, contest do NOT need quotes.
11. For date filtering, use timestamps: column >= '2024-01-01' or column::date = '2024-01-15'
```

**Why These Matter:**
- Rule 10: PostgreSQL requires quotes for mixed-case identifiers
- Rule 9: Prevents integer division errors in percentage calculations
- Rule 11: Ensures date comparisons work correctly

### 4. Database Knowledge
```
KNOWN DATA VALUES (use these for matching):
- Centers: 'IOI Bengaluru', 'IOI Delhi', 'IOI Noida', ..., 'PW Skills Bangalore', ...
- Batches: '23', '24', '25'
- Attendance status: 'PRESENT', 'ABSENT', 'LATE'
- Gender: 'MALE', 'FEMALE'
```

**Why:** Gives LLM real values to match against (better than hallucinating)

### 5. Pattern Reference
```
CRITICAL PATTERNS:
- "Current semester" means: use Student.semester_id to JOIN Semester
- "Nth semester" means: find Semester where number=N
- "Batch 24" means: WHERE Batch.name = '24'
- "sot" or "SOT" refers to the school/program
```

**Why:** Common question patterns explicitly explained to prevent errors

### 6. Attendance-Specific Patterns
```
Pattern for semester-specific attendance:
  JOIN "Attendance" A ON S.id = A.student_id
  JOIN "Class" Cl ON A.class_id = Cl.id
  JOIN "Semester" Sm ON Sm.division_id = S.division_id
  WHERE Cl.start_date >= Sm.start_date AND Cl.start_date <= Sm.end_date
```

**Why:** Attendance queries are complex; showing the pattern prevents errors

### 7. Business Filters (CRITICAL)
```
-- Example patterns with mandatory filters applied

-- STUDENT FILTER EXAMPLE:
WHERE S.is_active = true
  AND S.email NOT LIKE '%dummyemail%'
  AND C.name NOT LIKE '%PW Skills%'
  AND C.name != 'TEST Center'

-- CENTER FILTER EXAMPLE:
WHERE C.name NOT LIKE '%PW Skills%'
  AND C.name != 'TEST Center'
```

**Why:** Shows LLM exactly what filters to apply, with working examples

### 8. Schema Context
```
DATABASE SCHEMA:
{schema_context}
```

This is populated by context_builder.py with:
- 10 allowed tables only
- Column names and types
- Foreign key relationships
- Enum value options
- Sample data values
- Business rule notes

### 9. User Question
```
USER QUESTION: {question}
```

The actual question is inserted here.

### 10. Output Format
```
Generate ONLY the SQL query, nothing else.
No markdown, no explanation, no code blocks.
```

**Why:** Prevents LLM from wrapping SQL in code blocks (makes parsing harder)

## Response Generation Prompt

**File:** app/llm/prompts/templates.py::RESPONSE_GENERATION_PROMPT

**Purpose:** Format database results into natural language

**Key Elements:**
```
1. If results are empty, say so politely and suggest alternatives.
2. For single-value results (COUNT, AVG, SUM only), write a natural sentence.
3. For multiple rows, write a brief intro then the data will be shown in a table.
4. Keep responses concise and conversational.
5. If there was an error, explain it in simple terms.
6. Respond in the same language as the question.
7. NEVER list individual rows — the table formatter handles that.
```

**Why:**
- Single value → natural language ("There are 42 students")
- Multiple rows → table (not a list in natural language)
- Same language → respects user input language
- Table formatter handles UI → LLM doesn't try to format manually

## Prompt Injection Prevention

**Techniques Used:**

### 1. Locked System Instructions
```python
# System prompt is FIXED, not user-controllable
SYSTEM_PROMPT = """
You are an expert SQL query generator...
[Fixed, immutable rules]
"""

# User input is inserted into VARIABLE slots only
USER_PROMPT = f"USER QUESTION: {user_question}"
# NOT: USER_PROMPT = f"{user_question} - also run this: {attacker_input}"
```

### 2. Input Sanitization
```python
def sanitize_question(q: str) -> str:
    # Max 500 chars
    if len(q) > 500:
        raise ValueError("Too long")
    
    # No SQL keywords
    forbidden = ["INSERT", "DROP", "DELETE", "UPDATE"]
    if any(kw in q.upper() for kw in forbidden):
        raise ValueError("Forbidden keywords")
    
    return q.strip()
```

### 3. Role-Based Instructions
```
"You are a SQL Generator, NOT a Code Generator.
You cannot execute code.
You cannot run commands.
You cannot bypass security."
```

**Why This Works:**
- Explicit role prevents confusion
- "Cannot" is stronger than "do not" (more binding)
- Repeated constraints (defense in depth)

### 4. No Concatenation Shortcuts
```python
# ❌ BAD: Concatenates user input into system prompt
bad_prompt = f"You are SQL generator. {user_input}"

# ✓ GOOD: Inserts user input into clearly marked slot
good_prompt = SYSTEM_PROMPT + f"\nUSER QUESTION: {user_input}"
```

## Few-Shot Learning Examples

**Current SQL Generation Prompt Includes:**

### 1. Attendance Report (Full Pattern)
```sql
SELECT S.name, C.name AS center_name, B.name AS batch,
       ROUND(COUNT(CASE WHEN A.status = 'PRESENT' THEN 1 END) * 100.0 / 
       NULLIF(COUNT(*), 0), 1) AS attendance_pct
FROM "Student" S
JOIN "Attendance" A ON S.id = A.student_id
JOIN "Center" C ON S.center_id = C.id
JOIN "Batch" B ON S.batch_id = B.id
WHERE S.is_active = true
GROUP BY S.id, S.name, C.name, B.name
HAVING attendance_pct < 75
ORDER BY attendance_pct ASC
```

**Why:** Shows the exact pattern for complex aggregation

### 2. Semester-Specific Query (Join Pattern)
```sql
SELECT DISTINCT S.name, Sm.number
FROM "Student" S
JOIN "Semester" Sm ON S.division_id = Sm.division_id
WHERE S.is_active = true
AND Sm.number = 3
```

**Why:** Shows how to link student → division → semester

### 3. With Business Filters (Filter Pattern)
```sql
SELECT S.name, S.enrollment_id, C.name AS center
FROM "Student" S
JOIN "Center" C ON S.center_id = C.id
WHERE S.is_active = true
AND S.email NOT LIKE '%dummyemail%'
AND C.name NOT LIKE '%PW Skills%'
AND C.name != 'TEST Center'
```

**Why:** Shows all 4 mandatory filters in working example

## Progressive Prompt Improvement

**Current Issues to Address:**
1. ✓ Table restriction (will add)
2. ✓ Filter enforcement (will add)
3. ✓ Better examples (will add)
4. ✓ Ambiguity patterns (will add)

**Implementation Plan:**
1. Update templates.py with new prompts
2. Add table whitelist to schema context
3. Add filter validation to sql_validator.py
4. Test with sample queries
5. Iterate based on results

## Testing Prompts

**Test Case 1: Table Restriction**
```
Q: "How many coding problems have been solved?"
Expected: REJECT (problem table not allowed)
Actual: [Will test]
```

**Test Case 2: Filter Application**
```
Q: "All active students"
Expected: WHERE is_active = true AND email NOT LIKE '%dummyemail%'
Actual: [Will test]
```

**Test Case 3: Center Filtering**
```
Q: "Students in all centers"
Expected: WHERE center.name NOT LIKE '%PW Skills%' AND center.name != 'TEST Center'
Actual: [Will test]
```

**Test Case 4: Language Handling**
```
Q: "कितने छात्र हैं?" (Hindi: "How many students?")
Expected: Standard SQL (no Hindi in SQL)
Actual: [Will test]
```

## Prompt Maintenance

**When to Update Prompts:**
1. After observing repeated query generation errors
2. When new table/pattern is introduced
3. When business rules change
4. During major LLM model updates

**How to Update:**
1. Identify the issue from logs
2. Add clear example or constraint to prompt
3. Test with 5-10 sample questions
4. Log the change in git commit
5. Monitor for 1 week to ensure improvement

**Never:**
- Remove existing constraints
- Add user-controllable logic to system prompt
- Weaken security rules for convenience
