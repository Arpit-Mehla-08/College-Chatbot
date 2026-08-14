# Database Rules & Filtering Constraints

This document defines the STRICT database schema and filtering rules that MUST be applied to every query.

## Allowed Tables (EXACTLY 10)

These are the ONLY tables that should ever be used:

1. **Teacher** - Faculty members
2. **Center** - Physical campus locations
3. **Batch** - Student cohorts/batches
4. **School** - Schools/programs within centers
5. **Subject** - Academic subjects/courses
6. **Semester** - Academic periods
7. **Division** - Sub-groups within batches
8. **Class** - Scheduled class sessions
9. **Attendance** - Attendance records
10. **Student** - Student information

NO other tables should be referenced. Attempting to use other tables will cause query generation to fail.

---

## Mandatory Data Filtering Rules

These filters MUST be applied to EVERY query automatically:

### 1. Center Exclusions

#### PW Skills Centers (ALWAYS EXCLUDE)
```sql
WHERE center.name NOT LIKE '%PW Skills%'
```

**Examples of centers to exclude:**
- PW Skills Bangalore
- PW Skills Noida
- PW Skills Lucknow
- PW Skills Patna
- PW Skills Indore
- PW Skills Pune
- PW Skills Gurugram
- PW Skills Chandigarh
- PW Skills Chennai

**Why:** These are partner/franchise centers managed separately. They must not be included in queries.

#### TEST Center (ALWAYS EXCLUDE)
```sql
WHERE center.name != 'TEST Center'
```

**Why:** This is a test/development center and should never appear in production reports.

### 2. Student Filters

#### Active Students Only
```sql
WHERE student.is_active = true
```

**Why:** Inactive/graduated students should not be included in current operations queries.

#### Exclude Dummy Email Addresses
```sql
WHERE student.email NOT LIKE '%dummyemail%'
```

**Examples of dummy emails to exclude:**
- dummyemail180@gmail.com
- dummyemail@example.com
- Any email containing "dummyemail"

**Why:** These are test accounts and should never be in production queries.

### 3. Cascading Filters

When filtering centers, AUTOMATICALLY filter students:
```sql
-- If center is excluded, so are its students
WHERE s.center_id IN (
  SELECT id FROM "Center"
  WHERE name NOT LIKE '%PW Skills%'
  AND name != 'TEST Center'
)
```

---

## Implementation in Code

### Where to Apply Filters

1. **In SQL Generation Prompt** (app/llm/prompts/templates.py)
   - Add explicit examples showing these filters
   - Include them in the system prompt

2. **In Schema Context** (app/schema/context_builder.py)
   - Only include these 10 tables in schema context
   - Add note about mandatory filters

3. **In SQL Validator** (app/guardrails/sql_validator.py)
   - Add checks to ensure center filters are present
   - Add checks to ensure student filters are present

4. **In Query Execution** (app/db/connection.py)
   - As last-resort defense, add WHERE clause injection if missing

---

## Schema Reference

### Center
```
id (UUID)
name (STRING) - FILTER: NOT LIKE '%PW Skills%' AND != 'TEST Center'
location (STRING)
code (INT)
business_head (STRING)
academic_head (STRING)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Student
```
id (UUID)
name (STRING)
email (STRING) - FILTER: NOT LIKE '%dummyemail%'
phone (STRING)
gender (ENUM: MALE, FEMALE)
is_active (BOOLEAN) - FILTER: = true
enrollment_id (STRING)
center_id (UUID) - FK to Center
school_id (UUID) - FK to School
batch_id (UUID) - FK to Batch
semester_id (UUID) - FK to Semester
division_id (UUID) - FK to Division
joining_date (TIMESTAMP)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Teacher
```
id (UUID)
name (STRING)
email (STRING)
phone (STRING)
role (ENUM: TEACHER, etc.)
gender (ENUM: MALE, FEMALE)
center_id (UUID) - FK to Center
designation (STRING)
is_active (BOOLEAN)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Batch
```
id (UUID)
name (STRING) - e.g., "23", "24", "25"
center_id (UUID) - FK to Center
school_id (UUID) - FK to School
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### School
```
id (UUID)
name (ENUM: SchoolName)
center_id (UUID) - FK to Center
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Division
```
id (UUID)
code (STRING) - e.g., "A", "B", "C"
center_id (UUID) - FK to Center
batch_id (UUID) - FK to Batch
school_id (UUID) - FK to School
current_semester (UUID) - FK to Semester
start_date (TIMESTAMP)
end_date (TIMESTAMP)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Semester
```
id (UUID)
number (INT) - 1, 2, 3, etc.
division_id (UUID) - FK to Division
start_date (TIMESTAMP)
end_date (TIMESTAMP)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Subject
```
id (UUID)
name (STRING)
semester_id (UUID) - FK to Semester
credits (INT)
code (STRING)
teacher_id (UUID) - FK to Teacher
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Class
```
id (UUID)
lecture_number (STRING)
subject_id (UUID) - FK to Subject
division_id (UUID) - FK to Division
teacher_id (UUID) - FK to Teacher
room_id (UUID) - FK to Room (not in our 10 tables)
start_date (TIMESTAMP)
end_date (TIMESTAMP)
google_event_id (STRING)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

### Attendance
```
id (UUID)
student_id (UUID) - FK to Student
class_id (UUID) - FK to Class
status (ENUM: PRESENT, ABSENT, LATE)
successful_scan_count (INT)
marked_by (ENUM: MANUAL, SCAN)
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
```

---

## Identifier Composition Guide

### Complex Identifier Parsing

**Format: [Center Code][School Name][Batch Name][Division Code]**

Example: "1sot24b1"
```
1     = Center.code (IOI Bengaluru)
sot   = School.name (SOT - School of Technology)
24    = Batch.name (Batch 24)
b1    = Division.code (Division B1)
```

**Automatic Parsing in Queries:**
```sql
-- Extract components from composite identifier
WHERE c.code = 1                    -- Center
  AND s.name = 'SOT'                -- School
  AND b.name = '24'                 -- Batch
  AND d.code = 'B1'                 -- Division
  AND d.center_id = c.id            -- Ensure consistency
  AND b.school_id = s.id            -- Ensure consistency
```

**Always Validate:**
- Ensure all components exist in database
- Verify relationships are correct
- Return error if any component is invalid

---

## Date-Based Attendance Query Patterns

### Pattern: Attendance Percentage by Date Range

**Query Structure:**
1. First, calculate attendance % for each student in the date range
2. Then apply filters on the calculated percentage

**Example: Last 7 days, attendance < 30%**
```sql
WITH attendance_stats AS (
  SELECT
    s.id,
    s.name,
    s.enrollment_id,
    COUNT(a.id) as total_classes,
    COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) as present_count,
    ROUND(
      COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) * 100.0 /
      NULLIF(COUNT(a.id), 0),
      2
    ) as attendance_pct,
    ROUND(
      COUNT(CASE WHEN a.status = 'ABSENT' THEN 1 END) * 100.0 /
      NULLIF(COUNT(a.id), 0),
      2
    ) as absence_pct
  FROM "Student" s
  LEFT JOIN "Attendance" a ON s.id = a.student_id
  LEFT JOIN "Class" cl ON a.class_id = cl.id
  WHERE s.is_active = true
    AND s.email NOT LIKE '%dummyemail%'
    AND cl.start_date >= CURRENT_DATE - INTERVAL '7 days'
    AND cl.start_date < CURRENT_DATE + INTERVAL '1 day'
  GROUP BY s.id, s.name, s.enrollment_id
)
SELECT * FROM attendance_stats
WHERE attendance_pct < 30
  OR absence_pct > 70
ORDER BY attendance_pct ASC;
```

### Pattern: Continuously Absent in Date Range

**Query Structure:**
1. Filter classes in date range
2. Check which students have NO PRESENT records in that range

**Example: Continuously absent last 7 days**
```sql
SELECT s.id, s.name, s.enrollment_id,
       COUNT(DISTINCT a.created_at::date) as absent_days
FROM "Student" s
JOIN "Attendance" a ON s.id = a.student_id
JOIN "Class" cl ON a.class_id = cl.id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
  AND a.status = 'ABSENT'
  AND cl.start_date >= CURRENT_DATE - INTERVAL '7 days'
  AND cl.start_date < CURRENT_DATE + INTERVAL '1 day'
GROUP BY s.id, s.name, s.enrollment_id
HAVING COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) = 0
ORDER BY absent_days DESC;
```

### Pattern: Weekly Attendance Trend

**Query Structure:**
1. For each week in the range, calculate attendance %
2. Show week-over-week comparison

**Example: Last 4 weeks attendance trend**
```sql
WITH weekly_stats AS (
  SELECT
    s.id,
    s.name,
    EXTRACT(WEEK FROM cl.start_date) as week_number,
    EXTRACT(YEAR FROM cl.start_date) as year_number,
    COUNT(a.id) as total_classes,
    COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) as present_count,
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
  GROUP BY s.id, s.name, week_number, year_number
)
SELECT * FROM weekly_stats
ORDER BY s.id, year_number, week_number;
```

### Date Range Interpretation Guide

When user says "last 7 days":
```
TODAY = CURRENT_DATE
Range = CURRENT_DATE - INTERVAL '7 days' to TODAY + 1 day
PostgreSQL: WHERE date_column >= CURRENT_DATE - INTERVAL '7 days'
            AND date_column < CURRENT_DATE + INTERVAL '1 day'
```

When user says "last week":
```
OPTION 1 (Calendar Week: Mon-Sun):
  WHERE EXTRACT(WEEK FROM date_column) = EXTRACT(WEEK FROM CURRENT_DATE - INTERVAL '7 days')
  AND EXTRACT(YEAR FROM date_column) = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '7 days')

OPTION 2 (Rolling 7 days):
  WHERE date_column >= CURRENT_DATE - INTERVAL '7 days'
  AND date_column < CURRENT_DATE + INTERVAL '1 day'
```

When user says "this month":
```
WHERE EXTRACT(MONTH FROM date_column) = EXTRACT(MONTH FROM CURRENT_DATE)
  AND EXTRACT(YEAR FROM date_column) = EXTRACT(YEAR FROM CURRENT_DATE)
```

When user says "between DATE1 and DATE2":
```
WHERE date_column >= 'DATE1'::timestamp
  AND date_column <= 'DATE2'::timestamp + INTERVAL '1 day'
```

---

## Query Pattern Examples

### Pattern 1: Student-Centric Query with All Filters
```sql
SELECT s.name, s.email, c.name as center_name, b.name as batch
FROM "Student" s
JOIN "Center" c ON s.center_id = c.id
JOIN "Batch" b ON s.batch_id = b.id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
  AND c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
ORDER BY s.name;
```

### Pattern 2: Attendance Query with Filters
```sql
SELECT s.name, COUNT(*) as total_classes,
       COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) as present_count
FROM "Student" s
JOIN "Attendance" a ON s.id = a.student_id
JOIN "Class" cl ON a.class_id = cl.id
JOIN "Center" c ON s.center_id = c.id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
  AND c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
GROUP BY s.id, s.name
ORDER BY present_count DESC;
```

### Pattern 3: Subject/Class Query
```sql
SELECT subj.name, t.name as teacher, COUNT(cl.id) as class_count
FROM "Subject" subj
JOIN "Teacher" t ON subj.teacher_id = t.id
LEFT JOIN "Class" cl ON subj.id = cl.subject_id
JOIN "Division" d ON cl.division_id = d.id
JOIN "Center" c ON d.center_id = c.id
WHERE c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
GROUP BY subj.id, subj.name, t.id, t.name;
```

---

## Testing Filters

When testing query generation:
1. Verify every student query includes `s.is_active = true`
2. Verify every student query includes `s.email NOT LIKE '%dummyemail%'`
3. Verify every center query includes the center name filters
4. Verify no queries use tables outside the allowed 10
5. Test with actual center/student names that should be excluded

---

## Error Messages

If a query is generated without proper filters:
```
ERROR: Query missing mandatory filtering rules.
- Students must filter: is_active = true AND email NOT LIKE '%dummyemail%'
- Centers must filter: name NOT LIKE '%PW Skills%' AND name != 'TEST Center'
- Please regenerate with proper filters.
```

---

## Performance Considerations

- Filters should be applied at the WHERE clause level (not in JOIN conditions)
- Center name filters use LIKE which requires index on center.name
- is_active filter should use existing index on student.is_active
- Email filter may be expensive - only apply to student-centric queries
