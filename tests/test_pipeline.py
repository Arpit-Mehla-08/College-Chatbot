"""Tests for the core pipeline (with mocked LLM)."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from app.core.models import PipelineResult
from app.core.pipeline import run_pipeline
from app.db.connection import init_mock_db, reset_engine
from app.llm.base import AmbiguityResult, BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing pipeline flow."""

    def __init__(self, domain="students", sql="SELECT COUNT(*) as count FROM Student", ambiguous=False):
        self._domain = domain
        self._sql = sql
        self._ambiguous = ambiguous

    async def classify_domain(self, question: str) -> str:
        return self._domain

    async def generate_sql(self, question: str, schema_context: str) -> str:
        return self._sql

    async def generate_response(self, question, sql, results, error=None):
        if error:
            return f"Error: {error}"
        if results:
            return f"Found {len(results)} results."
        return "No results found."

    async def assess_ambiguity(self, question, schema_context):
        if self._ambiguous:
            return AmbiguityResult(
                is_ambiguous=True,
                clarifying_question="Do you mean attendance or exam performance?",
                ambiguity_type="unclear_metric",
            )
        return AmbiguityResult(is_ambiguous=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await reset_engine()
    await init_mock_db()
    yield
    await reset_engine()


class TestPipelineFlow:
    """Test the pipeline with mocked LLM."""

    @pytest.mark.asyncio
    async def test_successful_query(self):
        provider = MockLLMProvider(
            domain="students",
            sql="SELECT COUNT(*) as count FROM Student",
        )
        result = await run_pipeline("How many students?", provider=provider)
        assert result.error is None
        assert result.raw_results is not None
        assert result.raw_results[0]["count"] == 25
        assert result.domain == "students"
        assert result.sql == "SELECT COUNT(*) as count FROM Student"

    @pytest.mark.asyncio
    async def test_ambiguous_query(self):
        provider = MockLLMProvider(ambiguous=True)
        result = await run_pipeline("What is performance?", provider=provider)
        assert result.is_clarification
        assert "attendance or exam" in result.answer

    @pytest.mark.asyncio
    async def test_invalid_sql_retry(self):
        """Pipeline should retry once on validation failure."""
        call_count = 0

        class RetryProvider(MockLLMProvider):
            async def generate_sql(self, question, schema_context):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return "DROP TABLE Student"  # Invalid
                return "SELECT COUNT(*) as count FROM Student"  # Valid on retry

        provider = RetryProvider()
        result = await run_pipeline("How many students?", provider=provider)
        assert call_count == 2  # Called twice (retry)
        assert result.raw_results is not None
        assert result.raw_results[0]["count"] == 25

    @pytest.mark.asyncio
    async def test_empty_results(self):
        provider = MockLLMProvider(
            sql="SELECT * FROM Student WHERE name = 'NonExistent'"
        )
        result = await run_pipeline("Find NonExistent", provider=provider)
        assert result.raw_results == []
        assert result.row_count == 0

    @pytest.mark.asyncio
    async def test_execution_time_tracked(self):
        provider = MockLLMProvider()
        result = await run_pipeline("Count students", provider=provider)
        assert result.execution_time_ms is not None
        assert result.execution_time_ms > 0
