"""Tests for the response formatter."""

import pytest
from app.formatter.response_formatter import (
    format_results_basic,
    _format_table,
    _snake_to_title,
    _is_single_value_result,
)


class TestSnakeToTitle:
    def test_basic(self):
        assert _snake_to_title("student_name") == "Student Name"

    def test_id_suffix(self):
        result = _snake_to_title("student_id")
        assert "id" in result.lower()

    def test_lpa_suffix(self):
        result = _snake_to_title("package_lpa")
        assert "lpa" in result.lower()

    def test_single_word(self):
        assert _snake_to_title("name") == "Name"


class TestSingleValueDetection:
    def test_single_count(self):
        assert _is_single_value_result([{"count": 25}])

    def test_two_columns(self):
        assert _is_single_value_result([{"avg": 75.5, "total": 100}])

    def test_multi_row(self):
        assert not _is_single_value_result([{"name": "A"}, {"name": "B"}])

    def test_empty(self):
        assert not _is_single_value_result([])


class TestFormatTable:
    def test_basic_table(self):
        results = [
            {"name": "Aarav", "marks": 92},
            {"name": "Priya", "marks": 78},
        ]
        table = _format_table(results)
        assert "Aarav" in table
        assert "Priya" in table
        assert "Name" in table
        assert "Marks" in table

    def test_truncation(self):
        results = [{"id": i} for i in range(100)]
        table = _format_table(results, max_rows=10)
        assert "Showing first 10 of 100" in table

    def test_float_formatting(self):
        results = [{"score": 85.123}]
        table = _format_table(results)
        assert "85.12" in table

    def test_none_handling(self):
        results = [{"name": "Test", "value": None}]
        table = _format_table(results)
        assert "-" in table


class TestFormatResultsBasic:
    def test_empty_results(self):
        result = format_results_basic([], "any question")
        assert "No results" in result

    def test_single_value(self):
        result = format_results_basic([{"count": 42}], "how many?")
        assert "42" in result

    def test_multi_row(self):
        results = [{"name": "A", "score": 90}, {"name": "B", "score": 80}]
        result = format_results_basic(results, "show scores")
        assert "2" in result  # "Found 2 results"
        assert "A" in result
        assert "B" in result
