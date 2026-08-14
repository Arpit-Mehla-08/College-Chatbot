"""Tests for SQL validation guardrail."""

import pytest
from app.guardrails.sql_validator import validate_sql


class TestValidQueries:
    """Test that valid SELECT queries pass."""

    def test_simple_select(self):
        assert validate_sql("SELECT * FROM Student").is_valid

    def test_select_with_where(self):
        assert validate_sql("SELECT name FROM Student WHERE id = 1").is_valid

    def test_select_with_join(self):
        sql = "SELECT s.name, b.name FROM Student s JOIN Batch b ON s.batch_id = b.id"
        assert validate_sql(sql).is_valid

    def test_select_with_aggregation(self):
        sql = "SELECT COUNT(*) as cnt FROM Student GROUP BY center_id"
        assert validate_sql(sql).is_valid

    def test_select_with_subquery(self):
        sql = "SELECT * FROM Student WHERE id IN (SELECT student_id FROM Attendance)"
        assert validate_sql(sql).is_valid

    def test_cte_select(self):
        sql = "WITH cte AS (SELECT * FROM Student) SELECT * FROM cte"
        assert validate_sql(sql).is_valid

    def test_complex_cte(self):
        sql = """
        WITH week1 AS (
            SELECT student_id, COUNT(*) as cnt
            FROM Attendance WHERE attendance_date BETWEEN '2024-01-15' AND '2024-01-19'
            GROUP BY student_id
        ),
        week2 AS (
            SELECT student_id, COUNT(*) as cnt
            FROM Attendance WHERE attendance_date BETWEEN '2024-01-22' AND '2024-01-26'
            GROUP BY student_id
        )
        SELECT * FROM week1 JOIN week2 ON week1.student_id = week2.student_id
        """
        assert validate_sql(sql).is_valid

    def test_select_with_limit(self):
        assert validate_sql("SELECT * FROM Student LIMIT 10").is_valid

    def test_select_with_order_by(self):
        assert validate_sql("SELECT * FROM Student ORDER BY name DESC").is_valid


class TestInvalidQueries:
    """Test that dangerous queries are rejected."""

    def test_insert_rejected(self):
        r = validate_sql("INSERT INTO Student (name) VALUES ('hack')")
        assert not r.is_valid
        assert "INSERT" in r.error_message

    def test_update_rejected(self):
        r = validate_sql("UPDATE Student SET name = 'hack' WHERE id = 1")
        assert not r.is_valid

    def test_delete_rejected(self):
        r = validate_sql("DELETE FROM Student WHERE id = 1")
        assert not r.is_valid

    def test_drop_table_rejected(self):
        r = validate_sql("DROP TABLE Student")
        assert not r.is_valid

    def test_alter_table_rejected(self):
        r = validate_sql("ALTER TABLE Student ADD COLUMN hack TEXT")
        assert not r.is_valid

    def test_truncate_rejected(self):
        r = validate_sql("TRUNCATE TABLE Student")
        assert not r.is_valid

    def test_create_table_rejected(self):
        r = validate_sql("CREATE TABLE hack (id INT)")
        assert not r.is_valid

    def test_multi_statement_rejected(self):
        r = validate_sql("SELECT 1; DROP TABLE Student")
        assert not r.is_valid
        assert "Multiple" in r.error_message

    def test_empty_query_rejected(self):
        r = validate_sql("")
        assert not r.is_valid

    def test_none_query_rejected(self):
        r = validate_sql(None)
        assert not r.is_valid

    def test_too_long_query_rejected(self):
        sql = "SELECT " + "a" * 2001
        r = validate_sql(sql)
        assert not r.is_valid
        assert "length" in r.error_message

    def test_grant_rejected(self):
        r = validate_sql("GRANT ALL ON Student TO hacker")
        assert not r.is_valid
