"""
Benchmark test suite - 30+ questions covering all domains.

These tests validate that:
1. The SQL generated for each question is valid (passes guardrail)
2. The SQL executes successfully against the mock DB
3. The results match expected outcomes

Note: These tests use pre-written SQL (the "expected" queries) to validate
the mock DB data. In production, the LLM generates these queries dynamically.
"""

import asyncio
import pytest
import pytest_asyncio

from app.db.connection import init_mock_db, execute_read_query, reset_engine
from app.guardrails.sql_validator import validate_sql


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Initialize mock DB before each test module."""
    await reset_engine()
    await init_mock_db()
    yield
    await reset_engine()


# ============================================================
# DOMAIN: ATTENDANCE
# ============================================================

class TestAttendanceDomain:
    """Attendance-related queries."""

    @pytest.mark.asyncio
    async def test_attendance_above_90_percent(self):
        """Who had >90% attendance in week 2?"""
        sql = """
        SELECT s.name,
               COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*) as attendance_pct
        FROM Attendance a
        JOIN Student s ON s.id = a.student_id
        WHERE a.attendance_date BETWEEN '2024-01-22' AND '2024-01-26'
        GROUP BY s.name
        HAVING attendance_pct > 90
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) > 0
        names = [r["name"] for r in results]
        assert "Rahul Kumar" in names  # 100% week 2
        assert "Rohan Das" in names  # 100% week 2

    @pytest.mark.asyncio
    async def test_attendance_rise_30_percent(self):
        """Students whose attendance rose by 30% from week 1 to week 2."""
        sql = """
        WITH week1 AS (
            SELECT student_id,
                   COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM Attendance
            WHERE attendance_date BETWEEN '2024-01-15' AND '2024-01-19'
            GROUP BY student_id
        ),
        week2 AS (
            SELECT student_id,
                   COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM Attendance
            WHERE attendance_date BETWEEN '2024-01-22' AND '2024-01-26'
            GROUP BY student_id
        )
        SELECT s.name, w1.pct as week1_pct, w2.pct as week2_pct, (w2.pct - w1.pct) as change
        FROM week1 w1
        JOIN week2 w2 ON w1.student_id = w2.student_id
        JOIN Student s ON s.id = w1.student_id
        WHERE (w2.pct - w1.pct) >= 30
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        names = [r["name"] for r in results]
        # Priya: 40%->80% (+40), Rahul: 60%->100% (+40), Vikram: 20%->60% (+40), Amit: 20%->80% (+60)
        assert "Priya Patel" in names
        assert "Rahul Kumar" in names
        assert "Vikram Singh" in names
        assert "Amit Yadav" in names
        assert len(results) == 4

    @pytest.mark.asyncio
    async def test_center_specific_attendance(self):
        """Attendance for Center Mumbai students."""
        sql = """
        SELECT s.name,
               COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
        FROM Attendance a
        JOIN Student s ON s.id = a.student_id
        WHERE a.center_id = 2
        GROUP BY s.name
        ORDER BY pct DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) > 0
        # Rohan Das should have 100% (10/10 present)
        rohan = next(r for r in results if r["name"] == "Rohan Das")
        assert rohan["pct"] == 100.0

    @pytest.mark.asyncio
    async def test_student_count_per_center(self):
        """How many students in each center?"""
        sql = """
        SELECT c.name as center_name, COUNT(s.id) as student_count
        FROM Student s
        JOIN Center c ON s.center_id = c.id
        GROUP BY c.name
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 2
        delhi = next(r for r in results if r["center_name"] == "Center Delhi")
        mumbai = next(r for r in results if r["center_name"] == "Center Mumbai")
        assert delhi["student_count"] == 16
        assert mumbai["student_count"] == 9


# ============================================================
# DOMAIN: ACADEMICS
# ============================================================

class TestAcademicsDomain:
    """Exam and marks related queries."""

    @pytest.mark.asyncio
    async def test_top_5_math_students(self):
        """Top 5 students in Math Mid-Term."""
        sql = """
        SELECT s.name, sem.marks_obtained, sem.grade
        FROM StudentExamMarks sem
        JOIN Student s ON s.id = sem.student_id
        JOIN Exam e ON e.id = sem.exam_id
        WHERE e.name = 'Math Mid-Term' AND e.batch_id = 1
        ORDER BY sem.marks_obtained DESC
        LIMIT 5
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 5
        assert results[0]["name"] == "Aarav Sharma"
        assert results[0]["marks_obtained"] == 92.0

    @pytest.mark.asyncio
    async def test_average_marks_per_exam(self):
        """Average marks per exam."""
        sql = """
        SELECT e.name as exam_name, AVG(sem.marks_obtained) as avg_marks
        FROM StudentExamMarks sem
        JOIN Exam e ON e.id = sem.exam_id
        GROUP BY e.name
        ORDER BY avg_marks DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_students_with_grade_a_plus(self):
        """Students who got A+ in any exam."""
        sql = """
        SELECT s.name, e.name as exam_name, sem.marks_obtained
        FROM StudentExamMarks sem
        JOIN Student s ON s.id = sem.student_id
        JOIN Exam e ON e.id = sem.exam_id
        WHERE sem.grade = 'A+'
        ORDER BY sem.marks_obtained DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 3  # Aarav(Math), Priya(DS), Rohan(Math)

    @pytest.mark.asyncio
    async def test_batch_wise_performance(self):
        """Average marks by batch."""
        sql = """
        SELECT b.name as batch_name, AVG(sem.marks_obtained) as avg_marks
        FROM StudentExamMarks sem
        JOIN Student s ON s.id = sem.student_id
        JOIN Batch b ON b.id = s.batch_id
        GROUP BY b.name
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 2


# ============================================================
# DOMAIN: CODING
# ============================================================

class TestCodingDomain:
    """Coding platform queries."""

    @pytest.mark.asyncio
    async def test_problems_solved_by_student(self):
        """How many problems did Rohan Das solve?"""
        sql = """
        SELECT s.name, COUNT(DISTINCT sub.problem_id) as problems_solved
        FROM Submission sub
        JOIN Student s ON s.id = sub.student_id
        WHERE sub.status = 'accepted' AND s.name = 'Rohan Das'
        GROUP BY s.name
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 1
        assert results[0]["problems_solved"] == 7  # Solved 7 unique problems

    @pytest.mark.asyncio
    async def test_top_coders_by_problems_solved(self):
        """Top students by problems solved."""
        sql = """
        SELECT s.name, COUNT(DISTINCT sub.problem_id) as problems_solved
        FROM Submission sub
        JOIN Student s ON s.id = sub.student_id
        WHERE sub.status = 'accepted'
        GROUP BY s.name
        ORDER BY problems_solved DESC
        LIMIT 5
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) > 0
        assert results[0]["name"] == "Rohan Das"  # 7 problems

    @pytest.mark.asyncio
    async def test_contest_rankings(self):
        """Who ranked #1 in Weekly Contest 1?"""
        sql = """
        SELECT s.name, cp.score, cp.rank
        FROM ContestParticipation cp
        JOIN Student s ON s.id = cp.student_id
        JOIN Contest c ON c.id = cp.contest_id
        WHERE c.name = 'Weekly Contest 1'
        ORDER BY cp.rank
        LIMIT 5
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert results[0]["name"] == "Rohan Das"
        assert results[0]["rank"] == 1

    @pytest.mark.asyncio
    async def test_submissions_by_language(self):
        """Submissions breakdown by programming language."""
        sql = """
        SELECT language, COUNT(*) as submission_count,
               COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted_count
        FROM Submission
        GROUP BY language
        ORDER BY submission_count DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 3  # Python, Java, C++, JavaScript

    @pytest.mark.asyncio
    async def test_hard_problems_solved(self):
        """Students who solved hard problems."""
        sql = """
        SELECT s.name, p.title, p.difficulty
        FROM Submission sub
        JOIN Student s ON s.id = sub.student_id
        JOIN Problem p ON p.id = sub.problem_id
        WHERE sub.status = 'accepted' AND p.difficulty = 'hard'
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 1
        assert results[0]["name"] == "Rohan Das"


# ============================================================
# DOMAIN: CLUBS
# ============================================================

class TestClubsDomain:
    """Club-related queries."""

    @pytest.mark.asyncio
    async def test_coding_club_members_center_mumbai(self):
        """List members of Coding Club from Center Mumbai."""
        sql = """
        SELECT s.name, cm.role, cm.joined_date
        FROM ClubMember cm
        JOIN Student s ON s.id = cm.student_id
        JOIN Club cl ON cl.id = cm.club_id
        JOIN Center c ON c.id = cl.center_id
        WHERE cl.name = 'Coding Club' AND c.name = 'Center Mumbai'
        ORDER BY cm.role, s.name
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 3
        names = [r["name"] for r in results]
        assert "Rohan Das" in names

    @pytest.mark.asyncio
    async def test_club_presidents(self):
        """All club presidents."""
        sql = """
        SELECT s.name, cl.name as club_name, c.name as center_name
        FROM ClubMember cm
        JOIN Student s ON s.id = cm.student_id
        JOIN Club cl ON cl.id = cm.club_id
        JOIN Center c ON c.id = cl.center_id
        WHERE cm.role = 'president'
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 4  # 4 clubs, 4 presidents

    @pytest.mark.asyncio
    async def test_member_count_per_club(self):
        """How many members in each club?"""
        sql = """
        SELECT cl.name as club_name, c.name as center_name, COUNT(cm.id) as member_count
        FROM Club cl
        JOIN ClubMember cm ON cm.club_id = cl.id
        JOIN Center c ON c.id = cl.center_id
        GROUP BY cl.name, c.name
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 4


# ============================================================
# DOMAIN: PLACEMENTS
# ============================================================

class TestPlacementsDomain:
    """Placement-related queries."""

    @pytest.mark.asyncio
    async def test_placed_above_10_lpa(self):
        """Students placed with salary > 10 LPA."""
        sql = """
        SELECT s.name, p.company_name, p.role_title, p.package_lpa
        FROM Placement p
        JOIN Student s ON s.id = p.student_id
        WHERE p.package_lpa > 10 AND p.status IN ('accepted', 'offered')
        ORDER BY p.package_lpa DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 4  # Google(25), Microsoft(18), Amazon(16), Google(28), Flipkart(14), Adobe(20)
        assert all(r["package_lpa"] > 10 for r in results)

    @pytest.mark.asyncio
    async def test_average_placement_package(self):
        """Average placement package."""
        sql = """
        SELECT AVG(package_lpa) as avg_package
        FROM Placement
        WHERE status IN ('accepted', 'offered')
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 1
        assert results[0]["avg_package"] > 10  # Should be above 10 LPA average

    @pytest.mark.asyncio
    async def test_placements_by_company(self):
        """Placement count by company."""
        sql = """
        SELECT company_name, COUNT(*) as placed_count, AVG(package_lpa) as avg_package
        FROM Placement
        WHERE status IN ('accepted', 'offered')
        GROUP BY company_name
        ORDER BY avg_package DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 5

    @pytest.mark.asyncio
    async def test_highest_package(self):
        """Student with highest placement package."""
        sql = """
        SELECT s.name, p.company_name, p.package_lpa
        FROM Placement p
        JOIN Student s ON s.id = p.student_id
        WHERE p.status IN ('accepted', 'offered')
        ORDER BY p.package_lpa DESC
        LIMIT 1
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert results[0]["name"] == "Rohan Das"
        assert results[0]["package_lpa"] == 28.0


# ============================================================
# DOMAIN: STUDENTS
# ============================================================

class TestStudentsDomain:
    """Student info queries."""

    @pytest.mark.asyncio
    async def test_total_student_count(self):
        """How many students total?"""
        sql = "SELECT COUNT(*) as total_students FROM Student WHERE is_active = 1"
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert results[0]["total_students"] == 25

    @pytest.mark.asyncio
    async def test_students_per_batch(self):
        """Students per batch."""
        sql = """
        SELECT b.name as batch_name, COUNT(s.id) as student_count
        FROM Student s
        JOIN Batch b ON b.id = s.batch_id
        WHERE s.is_active = 1
        GROUP BY b.name
        ORDER BY student_count DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_students_in_center_delhi(self):
        """How many students in Center Delhi?"""
        sql = """
        SELECT COUNT(*) as count
        FROM Student s
        JOIN Center c ON s.center_id = c.id
        WHERE c.name = 'Center Delhi' AND s.is_active = 1
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert results[0]["count"] == 16


# ============================================================
# DOMAIN: PROJECTS
# ============================================================

class TestProjectsDomain:
    """Project-related queries."""

    @pytest.mark.asyncio
    async def test_top_projects_by_score(self):
        """Top projects by score."""
        sql = """
        SELECT s.name, p.title, p.tech_stack, p.score
        FROM Project p
        JOIN Student s ON s.id = p.student_id
        ORDER BY p.score DESC
        LIMIT 5
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert results[0]["title"] == "ML Pipeline"
        assert results[0]["score"] == 95.0

    @pytest.mark.asyncio
    async def test_projects_using_react(self):
        """Projects using React in tech stack."""
        sql = """
        SELECT s.name, p.title, p.tech_stack
        FROM Project p
        JOIN Student s ON s.id = p.student_id
        WHERE p.tech_stack LIKE '%React%'
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 2  # Chat App and E-commerce


# ============================================================
# DOMAIN: CERTIFICATIONS
# ============================================================

class TestCertificationsDomain:
    """Certification queries."""

    @pytest.mark.asyncio
    async def test_certifications_by_student(self):
        """Certifications obtained by Aarav Sharma."""
        sql = """
        SELECT c.name, c.issuing_org, c.issue_date
        FROM Certification c
        JOIN Student s ON s.id = c.student_id
        WHERE s.name = 'Aarav Sharma'
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 2  # AWS + Google

    @pytest.mark.asyncio
    async def test_certifications_by_org(self):
        """Certifications grouped by issuing org."""
        sql = """
        SELECT issuing_org, COUNT(*) as cert_count
        FROM Certification
        GROUP BY issuing_org
        ORDER BY cert_count DESC
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) >= 3

    @pytest.mark.asyncio
    async def test_students_with_aws_certs(self):
        """Students with AWS certifications."""
        sql = """
        SELECT s.name, c.name as cert_name
        FROM Certification c
        JOIN Student s ON s.id = c.student_id
        WHERE c.issuing_org = 'Amazon Web Services'
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 2  # Aarav and Rohan


# ============================================================
# DOMAIN: TREND/COMPARISON
# ============================================================

class TestTrendQueries:
    """Trend and comparison queries."""

    @pytest.mark.asyncio
    async def test_attendance_drop(self):
        """Students whose attendance dropped from week 1 to week 2."""
        sql = """
        WITH week1 AS (
            SELECT student_id,
                   COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM Attendance
            WHERE attendance_date BETWEEN '2024-01-15' AND '2024-01-19'
            GROUP BY student_id
        ),
        week2 AS (
            SELECT student_id,
                   COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM Attendance
            WHERE attendance_date BETWEEN '2024-01-22' AND '2024-01-26'
            GROUP BY student_id
        )
        SELECT s.name, w1.pct as week1_pct, w2.pct as week2_pct, (w1.pct - w2.pct) as drop_pct
        FROM week1 w1
        JOIN week2 w2 ON w1.student_id = w2.student_id
        JOIN Student s ON s.id = w1.student_id
        WHERE w1.pct > w2.pct
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        assert len(results) == 1  # Only Aarav dropped (100->60)
        assert results[0]["name"] == "Aarav Sharma"

    @pytest.mark.asyncio
    async def test_center2_attendance_improvement(self):
        """Center Mumbai students with attendance improvement."""
        sql = """
        WITH week1 AS (
            SELECT student_id,
                   COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM Attendance
            WHERE attendance_date BETWEEN '2024-01-15' AND '2024-01-19'
              AND center_id = 2
            GROUP BY student_id
        ),
        week2 AS (
            SELECT student_id,
                   COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) as pct
            FROM Attendance
            WHERE attendance_date BETWEEN '2024-01-22' AND '2024-01-26'
              AND center_id = 2
            GROUP BY student_id
        )
        SELECT s.name, w1.pct as week1_pct, w2.pct as week2_pct, (w2.pct - w1.pct) as change
        FROM week1 w1
        JOIN week2 w2 ON w1.student_id = w2.student_id
        JOIN Student s ON s.id = w1.student_id
        WHERE w2.pct > w1.pct
        """
        assert validate_sql(sql).is_valid
        results = await execute_read_query(sql)
        # Pooja: 80%->100% (+20), Amit: 40%->80% (+40)
        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "Pooja Verma" in names
        assert "Amit Yadav" in names
