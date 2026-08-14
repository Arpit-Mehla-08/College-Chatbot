-- Mock database schema for college chatbot development
-- Mirrors the key tables from the real PostgreSQL database

CREATE TABLE IF NOT EXISTS Center (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Batch (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    center_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (center_id) REFERENCES Center(id)
);

CREATE TABLE IF NOT EXISTS Student (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    batch_id INTEGER NOT NULL,
    center_id INTEGER NOT NULL,
    enrollment_date TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (batch_id) REFERENCES Batch(id),
    FOREIGN KEY (center_id) REFERENCES Center(id)
);

CREATE TABLE IF NOT EXISTS Subject (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS Class (
    id INTEGER PRIMARY KEY,
    subject_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    center_id INTEGER NOT NULL,
    instructor_name TEXT NOT NULL,
    class_date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES Subject(id),
    FOREIGN KEY (batch_id) REFERENCES Batch(id),
    FOREIGN KEY (center_id) REFERENCES Center(id)
);

CREATE TABLE IF NOT EXISTS Attendance (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    class_id INTEGER NOT NULL,
    center_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('present', 'absent', 'late')),
    FOREIGN KEY (student_id) REFERENCES Student(id),
    FOREIGN KEY (class_id) REFERENCES Class(id),
    FOREIGN KEY (center_id) REFERENCES Center(id)
);

CREATE TABLE IF NOT EXISTS Exam (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    exam_date TEXT NOT NULL,
    total_marks INTEGER NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES Subject(id),
    FOREIGN KEY (batch_id) REFERENCES Batch(id)
);

CREATE TABLE IF NOT EXISTS StudentExamMarks (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    exam_id INTEGER NOT NULL,
    marks_obtained REAL NOT NULL,
    grade TEXT,
    FOREIGN KEY (student_id) REFERENCES Student(id),
    FOREIGN KEY (exam_id) REFERENCES Exam(id)
);

CREATE TABLE IF NOT EXISTS Problem (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
    topic TEXT NOT NULL,
    points INTEGER NOT NULL DEFAULT 10
);

CREATE TABLE IF NOT EXISTS Submission (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    submitted_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('accepted', 'wrong_answer', 'time_limit', 'runtime_error')),
    language TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student(id),
    FOREIGN KEY (problem_id) REFERENCES Problem(id)
);

CREATE TABLE IF NOT EXISTS Contest (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    contest_date TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ContestParticipation (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    contest_id INTEGER NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    rank INTEGER,
    FOREIGN KEY (student_id) REFERENCES Student(id),
    FOREIGN KEY (contest_id) REFERENCES Contest(id)
);

CREATE TABLE IF NOT EXISTS Club (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    center_id INTEGER NOT NULL,
    FOREIGN KEY (center_id) REFERENCES Center(id)
);

CREATE TABLE IF NOT EXISTS ClubMember (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    role TEXT DEFAULT 'member',
    joined_date TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Student(id),
    FOREIGN KEY (club_id) REFERENCES Club(id)
);

CREATE TABLE IF NOT EXISTS Placement (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    role_title TEXT NOT NULL,
    package_lpa REAL NOT NULL,
    placement_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('offered', 'accepted', 'rejected')),
    FOREIGN KEY (student_id) REFERENCES Student(id)
);

CREATE TABLE IF NOT EXISTS Project (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    tech_stack TEXT,
    submitted_date TEXT NOT NULL,
    score REAL,
    FOREIGN KEY (student_id) REFERENCES Student(id)
);

CREATE TABLE IF NOT EXISTS Certification (
    id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    issuing_org TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    expiry_date TEXT,
    FOREIGN KEY (student_id) REFERENCES Student(id)
)
