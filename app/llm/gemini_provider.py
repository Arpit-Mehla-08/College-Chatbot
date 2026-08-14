"""Google Gemini LLM provider implementation using google.genai SDK."""

import asyncio
import json
import logging
import re
import openai

from app.core.config import settings
from app.llm.base import AmbiguityResult, BaseLLMProvider
from app.llm.prompts.templates import (
    AMBIGUITY_ASSESSMENT_PROMPT,
    DOMAIN_CLASSIFICATION_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    SQL_GENERATION_PROMPT,
    TREND_SQL_GENERATION_PROMPT,
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider using the new google.genai SDK."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")

        self.client = openai.OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )

        self.model = settings.GEMINI_MODEL

    async def _generate(self, prompt: str) -> str:
        """Generate text from a prompt with retry and exponential backoff."""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                logger.debug(f"[Gemini] Calling LLM (attempt {attempt + 1}/{max_retries})...")
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=prompt,
                )
                logger.debug(f"[Gemini] LLM response received ({len(response.text)} chars)")
                return response.text.strip()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"[Gemini] LLM request failed after {max_retries} attempts: {e}")
                    raise RuntimeError(
                        f"LLM request failed after {max_retries} attempts: {str(e)}"
                    ) from e
                delay = base_delay * (2 ** attempt)
                logger.warning(f"[Gemini] Attempt {attempt + 1} failed, retrying in {delay}s...")
                await asyncio.sleep(delay)

    async def classify_domain(self, question: str) -> str:
        """Classify question into a domain."""
        prompt = DOMAIN_CLASSIFICATION_PROMPT.format(question=question)
        result = await self._generate(prompt)
        # Clean up response - should be a single word
        domain = result.lower().strip().split("\n")[0].split(" ")[0]
        valid_domains = [
            "attendance", "academics", "coding", "clubs",
            "placements", "students", "projects", "certifications",
            "general", "out_of_scope",
        ]
        if domain not in valid_domains:
            return "general"
        return domain

    async def generate_sql(self, question: str, schema_context: str) -> str:
        """Generate SQL from natural language question."""
        # Detect if this is a trend/comparison query
        trend_keywords = [
            "change", "trend", "compare", "comparison", "increase",
            "decrease", "raised", "dropped", "improved", "declined",
            "week over week", "week-over-week", "period", "growth",
            "rose", "fell", "difference", "delta",
        ]
        is_trend = any(kw in question.lower() for kw in trend_keywords)

        if is_trend:
            logger.debug("Question detected as trend/comparison query")
            from app.core.week_utils import get_week_context_for_prompt
            prompt = TREND_SQL_GENERATION_PROMPT.format(
                question=question,
                schema_context=schema_context,
                week_definition=settings.WEEK_DEFINITION,
                week_context=get_week_context_for_prompt(),
            )
        else:
            prompt = SQL_GENERATION_PROMPT.format(
                question=question,
                schema_context=schema_context,
            )

        logger.debug("Calling Gemini to generate SQL...")
        result = await self._generate(prompt)
        # Clean up: remove markdown code blocks if present
        result = re.sub(r"```sql\s*", "", result)
        result = re.sub(r"```\s*", "", result)
        # Remove trailing semicolons
        result = result.strip().rstrip(";")
        logger.debug(f"SQL generation complete: {result[:100]}...")
        return result

    async def generate_response(
        self, question: str, sql: str, results: list[dict], error: str | None = None
    ) -> str:
        """Generate natural language response from results."""
        # Truncate results for prompt if too many
        display_results = results[:5] if len(results) > 5 else results
        results_str = json.dumps(display_results, default=str)

        prompt = RESPONSE_GENERATION_PROMPT.format(
            question=question,
            sql=sql,
            results=results_str,
            row_count=len(results),
            error=error or "None",
        )
        return await self._generate(prompt)

    async def assess_ambiguity(
        self, question: str, schema_context: str
    ) -> AmbiguityResult:
        """Assess whether a question is ambiguous."""
        prompt = AMBIGUITY_ASSESSMENT_PROMPT.format(
            question=question,
            schema_context=schema_context,
        )
        result = await self._generate(prompt)

        # Parse JSON response
        try:
            # Clean up markdown if present
            result = re.sub(r"```json\s*", "", result)
            result = re.sub(r"```\s*", "", result)
            parsed = json.loads(result)
            return AmbiguityResult(
                is_ambiguous=parsed.get("is_ambiguous", False),
                clarifying_question=parsed.get("clarifying_question"),
                ambiguity_type=parsed.get("ambiguity_type"),
            )
        except (json.JSONDecodeError, KeyError):
            # If parsing fails, assume not ambiguous
            return AmbiguityResult(is_ambiguous=False)
