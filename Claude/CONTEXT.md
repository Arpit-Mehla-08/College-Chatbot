# Database Context & Reference

Complete reference of the database schema, relationships, and sample data.

## Quick Reference

### 10 Allowed Tables

| Table | Purpose | Key Columns | Sample IDs |
|-------|---------|-------------|-----------|
| **Student** | Learners enrolled | id, name, email, is_active, center_id | e991bfb3-860a... |
| **Teacher** | Faculty & instructors | id, name, email, center_id, is_active | 01dbb1cc-8f35... |
| **Center** | Campus locations | id, name, location, code | 4a174eab-ccd1... |
| **Batch** | Student cohorts | id, name, center_id, school_id | 65c5d14b-31ee... |
| **School** | Schools/programs | id, name, center_id | 17578e8a-e77f... |
| **Division** | Batch sub-groups | id, code, batch_id, center_id | cae2ae5c-9728... |
| **Semester** | Academic periods | id, number, division_id | 90beca32-9837... |
| **Subject** | Courses | id, name, semester_id, teacher_id | d8d542e3-32c5... |
| **Class** | Scheduled sessions | id, subject_id, teacher_id, start_date | 1a73bc8b-238d... |
| **Attendance** | Presence records | id, student_id, class_id, status | 4ff1efef-8721... |

---

## Complete Schema Reference

### 1. Student Table

```
id (UUID) - Primary key
name (STRING) - Student full name
email (STRING) - Email address - UNIQUE
phone (STRING) - Phone number - UNIQUE
gender (ENUM) - MALE, FEMALE
is_active (BOOLEAN) - true = currently enrolled, false = dropped/graduated
enrollment_id (STRING) - Enrollment number - UNIQUE
joining_date (TIMESTAMP) - When student joined - Default: 2010-01-01
center_id (UUID) - FK to Center
school_id (UUID) - FK to School
batch_id (UUID) - FK to Batch
semester_id (UUID) - FK to Semester
division_id (UUID) - FK to Division
cohort_id (UUID) - FK to Cohort (optional)
degree_id (UUID) - FK to ExternalDegree (optional)
device_id (STRING) - Device ID (optional)
googleId (STRING) - Google OAuth ID (optional) - EXCLUDED FROM SCHEMA
firstLoggedIn (BOOLEAN) - Default: false
lastLoginAt (TIMESTAMP) - Last login time
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Filters Applied:**
```sql
WHERE is_active = true
AND email NOT LIKE '%dummyemail%'
```

**Sample Data:**
- Name: Aadhaar Goel
- Email: aadhaar.sot010001@pwioi.com
- Enrollment: 2301010001
- Gender: MALE
- Phone: 9667896164
- Is Active: true

### 2. Teacher Table

```
id (UUID) - Primary key
name (STRING) - Teacher full name
email (STRING) - Email address - UNIQUE
phone (STRING) - Phone number - UNIQUE
role (ENUM) - TEACHER (and others)
gender (ENUM) - MALE, FEMALE (optional)
designation (STRING) - Job title (optional)
center_id (UUID) - FK to Center
photo (STRING) - S3 key for profile photo (optional)
linkedin (STRING) - LinkedIn profile (optional)
github_link (STRING) - GitHub profile (optional)
personal_mail (STRING) - Personal email (optional)
pwId (STRING) - PW ID (optional) - UNIQUE
is_active (BOOLEAN) - true = currently employed
supervising_teacher_id (UUID) - FK to Teacher (optional)
googleId (STRING) - Google OAuth ID (optional) - EXCLUDED FROM SCHEMA
about (STRING) - Bio/description (optional)
lastLoginAt (TIMESTAMP) - Last login
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Sample Data:**
- Name: Kinjal Sengupta
- Email: kinjal.sengupta@pw.live
- Phone: 8007959665
- Role: TEACHER
- Gender: FEMALE
- Is Active: false
- PwId: PW19272

### 3. Center Table

```
id (UUID) - Primary key
name (STRING) - Center name
location (STRING) - City/address
code (INT) - Numeric code - UNIQUE
business_head (UUID) - FK to Admin (optional)
academic_head (UUID) - FK to Admin (optional)
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Filters Applied:**
```sql
WHERE name NOT LIKE '%PW Skills%'
AND name != 'TEST Center'
```

**Sample Data - IOI Centers (INCLUDED):**
- IOI Bengaluru (code: 1)
- IOI Delhi (code: 2)
- IOI Noida (code: 3)
- IOI Pune (code: 4)
- IOI Patna (code: 5)
- IOI Lucknow (code: 6)
- IOI Indore (code: 7)

**Sample Data - PW Skills Centers (EXCLUDED):**
- PW Skills Bangalore (LIKE '%PW Skills%')
- PW Skills Noida (LIKE '%PW Skills%')
- PW Skills Lucknow (LIKE '%PW Skills%')
- PW Skills Patna (LIKE '%PW Skills%')
- PW Skills Indore (LIKE '%PW Skills%')
- PW Skills Pune (LIKE '%PW Skills%')
- PW Skills Gurugram (LIKE '%PW Skills%')
- PW Skills Chandigarh (LIKE '%PW Skills%')
- PW Skills Chennai (LIKE '%PW Skills%')

**Special Centers (EXCLUDED):**
- TEST Center (= 'TEST Center')

### 4. Batch Table

```
id (UUID) - Primary key
name (STRING) - Batch name/number (e.g., "23", "24", "25")
center_id (UUID) - FK to Center
school_id (UUID) - FK to School
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Sample Data:**
- Name: "23" - Batch 23
- Name: "24" - Batch 24
- Name: "OTT24" - Online Training Batch

### 5. School Table

```
id (UUID) - Primary key
name (ENUM SchoolName) - School/program name
center_id (UUID) - FK to Center
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Constraint:** UNIQUE(center_id, name) - One school per center

**Sample Data:**
- SOT - School of Technology (IOI program)
- SOM - School of Management

### 6. Division Table

```
id (UUID) - Primary key
code (STRING) - Division code (e.g., "A", "B", "C")
center_id (UUID) - FK to Center
batch_id (UUID) - FK to Batch
school_id (UUID) - FK to School
current_semester (UUID) - FK to Semester (optional) - UNIQUE
start_date (TIMESTAMP) - When division started
end_date (TIMESTAMP) - When division ends (optional)
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Sample Data:**
- Code: "B2" - Batch 2, Division B
- Code: "B1" - Batch 1, Division B
- Code: "A" - Batch A, Division A

### 7. Semester Table

```
id (UUID) - Primary key
number (INT) - Semester number (1, 2, 3, 4, ...)
division_id (UUID) - FK to Division
start_date (TIMESTAMP) - Semester start date
end_date (TIMESTAMP) - Semester end date (optional/NULL)
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Relationships:**
- Semester belongs to Division (many-to-one)
- Division can have multiple Semesters
- Student enrolled in one Semester at a time

**Sample Data:**
- Number: 1 - First semester
- Number: 3 - Third semester
- Number: 4 - Fourth semester

### 8. Subject Table

```
id (UUID) - Primary key
name (STRING) - Subject name
semester_id (UUID) - FK to Semester
credits (INT) - Credit hours
code (STRING) - Subject code (e.g., "PDM303", "IOI102")
teacher_id (UUID) - FK to Teacher
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Sample Data:**
- Name: Product Management
- Code: PDM303
- Credits: 3
- Name: Web Development
- Code: IOI102
- Credits: 4

### 9. Class Table

```
id (UUID) - Primary key
lecture_number (STRING) - Lecture sequence number
subject_id (UUID) - FK to Subject
division_id (UUID) - FK to Division
teacher_id (UUID) - FK to Teacher
room_id (UUID) - FK to Room (NOT IN OUR 10 TABLES)
start_date (TIMESTAMP) - Class start time
end_date (TIMESTAMP) - Class end time
google_event_id (STRING) - Google Calendar event ID
created_at (TIMESTAMP) - Record creation
updated_at (TIMESTAMP) - Last update
```

**Indexes:**
- (division_id, start_date)
- (subject_id)
- (division_id)
- (teacher_id)
- (room_id)

**Sample Data:**
- Lecture Number: "1"
- Start Date: September 1, 2025, 3:45 AM
- End Date: September 1, 2025, 5:00 AM
- Lecture Number: "2"
- Start Date: September 2, 2025, 5:15 AM
- End Date: September 2, 2025, 6:30 AM

### 10. Attendance Table

```
id (UUID) - Primary key
student_id (UUID) - FK to Student
class_id (UUID) - FK to Class
status (ENUM) - PRESENT, ABSENT, LATE
successful_scan_count (INT) - Number of beacon scans (default: 3)
marked_by (ENUM) - MANUAL, SCAN (how attendance was marked)
created_at (TIMESTAMP) - When record was created
updated_at (TIMESTAMP) - Last update
```

**Constraints:**
- UNIQUE(student_id, class_id) - One attendance per student per class

**Indexes:**
- (student_id, created_at)
- (created_at)
- (student_id)
- (class_id)

**Sample Data:**
- Status: PRESENT
- Status: ABSENT
- Status: LATE
- Marked By: MANUAL
- Successful Scan Count: 3 or 0

---

## Relationships (Foreign Keys)

### Hierarchy
```
Center
├─ Batch
│  └─ Division
│      ├─ Semester
│      │  └─ Subject
│      │      └─ Class
│      │          └─ Attendance ← Student
│      └─ Student
├─ School
│  ├─ Batch
│  └─ Student
└─ Teacher
   └─ Subject
      └─ Class
         └─ Attendance ← Student
```

### Key JOIN Paths

**Find student's attendance:**
```
Student → Attendance → Class → Division → Semester
                    ↓
                  Subject
                    ↓
                  Teacher
```

**Find division's classes:**
```
Division → Class ← Subject ← Semester ← Division
Class ← Teacher
Class → Attendance → Student
```

**Find center's students:**
```
Center → Batch → Division → Student
Center → School → Batch → Division → Student
```

---

## Enum Types

### Gender
- MALE
- FEMALE

### Attendance Status
- PRESENT
- ABSENT
- LATE

### Attendance Marked By
- MANUAL
- SCAN

### Teacher Role
- TEACHER
- (others exist but not detailed)

### School Name
- SOT (School of Technology)
- SOM (School of Management)
- (others may exist)

### Job Type (in Placement - NOT IN OUR SCOPE)
- INTERNSHIP
- FULL_TIME

### Work Mode (in Placement - NOT IN OUR SCOPE)
- REMOTE
- ONSITE
- HYBRID

### Problem Difficulty (coding platform - NOT IN OUR SCOPE)
- EASY
- MEDIUM
- HARD

---

## Data Type Reference

| Type | Example | PostgreSQL Type | Notes |
|------|---------|-----------------|-------|
| UUID | e991bfb3-860a... | UUID/TEXT | All IDs |
| String | "IOI Bengaluru" | VARCHAR | Names, emails |
| Int | 23 (batch number) | INTEGER | Counts, codes |
| Enum | PRESENT | VARCHAR/ENUM | Predefined set |
| Boolean | true, false | BOOLEAN | Flags (is_active) |
| Timestamp | 2025-09-01 03:45 | TIMESTAMP | Dates/times |

---

## Common Query Patterns

### Pattern 1: Count Active Students by Center
```sql
SELECT c.name AS center, COUNT(s.id) AS student_count
FROM "Center" c
LEFT JOIN "Student" s ON c.id = s.center_id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
  AND c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
GROUP BY c.id, c.name
ORDER BY student_count DESC;
```

### Pattern 2: Attendance by Student
```sql
SELECT s.name, s.enrollment_id,
       COUNT(a.id) AS total_classes,
       COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) AS present,
       ROUND(COUNT(CASE WHEN a.status = 'PRESENT' THEN 1 END) * 100.0 / 
             NULLIF(COUNT(a.id), 0), 2) AS attendance_pct
FROM "Student" s
LEFT JOIN "Attendance" a ON s.id = a.student_id
JOIN "Center" c ON s.center_id = c.id
WHERE s.is_active = true
  AND s.email NOT LIKE '%dummyemail%'
  AND c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
GROUP BY s.id, s.name, s.enrollment_id
ORDER BY attendance_pct ASC;
```

### Pattern 3: Classes by Teacher
```sql
SELECT t.name AS teacher, COUNT(cl.id) AS class_count,
       STRING_AGG(DISTINCT s.name, ', ') AS subjects
FROM "Teacher" t
LEFT JOIN "Class" cl ON t.id = cl.teacher_id
LEFT JOIN "Subject" s ON cl.subject_id = s.id
JOIN "Center" c ON t.center_id = c.id
WHERE c.name NOT LIKE '%PW Skills%'
  AND c.name != 'TEST Center'
  AND t.is_active = true
GROUP BY t.id, t.name
ORDER BY class_count DESC;
```

---

## Performance Considerations

### Indexes Present
- student: (division_id, batch_id)
- center: (business_head), (academic_head)
- batch: (center_id), (school_id)
- division: (batch_id), (center_id), (school_id), (current_semester)
- class: (division_id, start_date), (subject_id), (teacher_id), (room_id)
- attendance: (student_id, created_at), (created_at), (student_id), (class_id)
- subject: (semester_id), (teacher_id)
- semester: (division_id)
- teacher: (center_id), (supervising_teacher_id)

### Query Optimization Tips
1. Always filter for active students early
2. Use (division_id, start_date) index for date range queries
3. Filter centers before joining to students
4. Use NULLIF to prevent division by zero
5. Aggregate at query level, not application level

---

## Data Quality Notes

- Student emails are unique and must be valid
- Teacher emails are unique
- Phone numbers are unique per person
- Enrollment IDs are unique per student
- UUIDs are used for all primary keys (text type)
- Timestamps include timezone info in production
- Some fields like cohort_id and degree_id are optional
- Google OAuth fields are excluded from schema context
