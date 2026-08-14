"""Tests for schema introspection and context builder."""

import pytest
import pytest_asyncio

from app.db.connection import init_mock_db, reset_engine
from app.schema.introspector import get_table_names, get_table_columns, get_full_schema
from app.schema.context_builder import (
    build_schema_context,
    get_available_domains,
    get_domain_tables,
    load_annotations,
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Initialize mock DB."""
    await reset_engine()
    await init_mock_db()
    yield
    await reset_engine()


class TestIntrospector:
    """Test schema introspection."""

    @pytest.mark.asyncio
    async def test_get_table_names(self):
        tables = await get_table_names()
        assert "Student" in tables
        assert "Attendance" in tables
        assert "Exam" in tables
        assert len(tables) >= 15

    @pytest.mark.asyncio
    async def test_get_student_columns(self):
        cols = await get_table_columns("Student")
        col_names = [c["column_name"] for c in cols]
        assert "id" in col_names
        assert "name" in col_names
        assert "batch_id" in col_names
        assert "center_id" in col_names

    @pytest.mark.asyncio
    async def test_get_full_schema(self):
        schema = await get_full_schema()
        assert "Student" in schema
        assert len(schema["Student"]) >= 5


class TestContextBuilder:
    """Test schema context builder."""

    def test_available_domains(self):
        domains = get_available_domains()
        assert "attendance" in domains
        assert "academics" in domains
        assert "coding" in domains
        assert "clubs" in domains
        assert "placements" in domains

    def test_domain_tables(self):
        tables = get_domain_tables("attendance")
        assert "Attendance" in tables
        assert "Student" in tables
        assert "Class" in tables
        # Should NOT include unrelated tables
        assert "Placement" not in tables

    @pytest.mark.asyncio
    async def test_build_attendance_context(self):
        ctx = await build_schema_context("attendance")
        assert "Attendance" in ctx
        assert "Student" in ctx
        assert "present" in ctx  # From notes
        # Table section should not have Placement table header
        assert "**Placement**" not in ctx

    @pytest.mark.asyncio
    async def test_build_full_context(self):
        ctx = await build_schema_context(None)
        assert "Student" in ctx
        assert "Attendance" in ctx
        assert "Placement" in ctx

    def test_annotations_load(self):
        ann = load_annotations()
        assert "domains" in ann
        assert "tables" in ann
        assert "relationships" in ann

    @pytest.mark.asyncio
    async def test_excluded_columns(self):
        ctx = await build_schema_context("students")
        # phone and email should be excluded
        assert "phone" not in ctx.lower() or "Phone" not in ctx
