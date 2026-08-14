"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AmbiguityResult:
    """Result of ambiguity assessment."""
    is_ambiguous: bool
    clarifying_question: str | None = None
    ambiguity_type: str | None = None  # "unclear_metric", "missing_filter", "multiple_tables"


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers. Implement this to add new LLM backends."""

    @abstractmethod
    async def classify_domain(self, question: str) -> str:
        """
        Classify the user's question into a domain category.

        Returns one of: attendance, academics, coding, clubs, placements,
        students, projects, certifications, general, out_of_scope
        """
        ...

    @abstractmethod
    async def generate_sql(self, question: str, schema_context: str) -> str:
        """
        Generate a SQL SELECT query from the user's natural language question.

        Args:
            question: The user's question (may be in English, Hindi, or Hinglish)
            schema_context: Formatted schema context for the relevant domain

        Returns:
            A SQL SELECT query string.
        """
        ...

    @abstractmethod
    async def generate_response(
        self, question: str, sql: str, results: list[dict], error: str | None = None
    ) -> str:
        """
        Generate a natural language response from query results.

        Args:
            question: Original user question
            sql: The SQL that was executed
            results: Query results as list of dicts
            error: Error message if query failed

        Returns:
            Human-friendly response string.
        """
        ...

    @abstractmethod
    async def assess_ambiguity(
        self, question: str, schema_context: str
    ) -> AmbiguityResult:
        """
        Assess whether a question is ambiguous and needs clarification.

        Args:
            question: The user's question
            schema_context: Available schema context

        Returns:
            AmbiguityResult with clarification info if needed.
        """
        ...
