"""Core NL-to-SQL pipeline - orchestrates the full question-to-answer flow."""

import logging
import time
from typing import Optional

from app.core.models import PipelineResult
from app.db.connection import execute_read_query
from app.guardrails.sql_validator import validate_sql
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_provider
from app.schema.context_builder import build_schema_context


MAX_SQL_RETRIES = 3


async def _generate_and_execute_sql(
    llm: BaseLLMProvider,
    question: str,
    schema_context: str,
    attempt: int = 1,
    previous_sql: str | None = None,
    previous_error: str | None = None,
) -> tuple[str, list[dict] | None, str | None]:
    """
    Generate SQL, validate, and execute. Returns (sql, results, error).

    If previous attempts failed, includes that context for the LLM to learn from.
    """
    log = logging.getLogger(__name__)

    # Build the prompt with retry context if needed
    if previous_error and previous_sql:
        log.debug(f"[Attempt {attempt}] Retrying with feedback from previous attempt")
        log.debug(f"  Previous SQL: {previous_sql[:100]}...")
        log.debug(f"  Previous error: {previous_error[:100]}...")
        prompt_question = (
            f"{question}\n\n"
            f"PREVIOUS ATTEMPT (failed): {previous_sql}\n"
            f"ERROR/ISSUE: {previous_error}\n"
            f"Generate a DIFFERENT query that avoids this issue. "
            f"Try a simpler approach - maybe fewer JOINs or looser filters."
        )
    else:
        prompt_question = question

    # Generate SQL
    log.info(f"[Attempt {attempt}] Generating SQL from question: {question[:80]}...")
    sql = await llm.generate_sql(prompt_question, schema_context)
    log.info(f"[Attempt {attempt}] Generated SQL: {sql}")

    # Validate
    log.debug(f"[Attempt {attempt}] Validating SQL...")
    validation = validate_sql(sql)
    if not validation.is_valid:
        error_msg = f"Invalid SQL: {validation.error_message}"
        log.warning(f"[Attempt {attempt}] SQL validation failed: {error_msg}")
        return sql, None, error_msg

    log.info(f"[Attempt {attempt}] SQL validation passed ✓")

    # Execute
    log.info(f"[Attempt {attempt}] Executing SQL query...")
    try:
        results = await execute_read_query(validation.sanitized_sql)
        log.info(f"[Attempt {attempt}] Query executed successfully ✓ | Results: {len(results)} rows")
        return sql, results, None
    except RuntimeError as e:
        error_msg = f"Execution error: {str(e)}"
        log.error(f"[Attempt {attempt}] Query execution failed: {error_msg}")
        return sql, None, error_msg


async def run_pipeline(
    question: str,
    conversation_context: Optional[str] = None,
    provider: Optional[BaseLLMProvider] = None,
) -> PipelineResult:
    """
    Run the full NL-to-SQL pipeline with self-healing retry.

    Flow:
    1. Classify domain
    2. Build schema context
    3. (Optional) Assess ambiguity for very short questions
    4. Generate SQL → Validate → Execute
    5. If no results or error: retry with feedback (up to 3 attempts)
    6. Return results

    The retry mechanism feeds the failed SQL and error back to the LLM
    so it can generate a better query on each attempt.
    """
    log = logging.getLogger(__name__)
    start_time = time.time()
    llm = provider or get_provider()

    log.info("=" * 80)
    log.info(f"PIPELINE START | Question: {question}")
    log.info("=" * 80)

    # If there's conversation context (answer to a clarification), combine it
    effective_question = question
    if conversation_context:
        log.debug(f"Including conversation context: {conversation_context[:100]}...")
        effective_question = f"{conversation_context}\nUser's answer: {question}"

    try:
        # Step 1: Classify domain
        log.info("Step 1: Classifying domain...")
        domain = await llm.classify_domain(effective_question)
        log.info(f"Step 1 ✓ Domain classified as: {domain}")

        # Step 1.5: Reject out-of-scope questions immediately
        if domain == "out_of_scope":
            log.warning("Question classified as out-of-scope")
            elapsed = (time.time() - start_time) * 1000
            return PipelineResult(
                answer=(
                    "I can only answer questions related to the college database — "
                    "such as students, attendance, exams, placements, coding contests, "
                    "clubs, projects, and certifications. Please ask a relevant question."
                ),
                domain=domain,
                execution_time_ms=elapsed,
            )

        # Step 2: Build schema context
        log.info("Step 2: Building schema context...")
        schema_context = await build_schema_context(domain)
        log.info(f"Step 2 ✓ Schema context ready (length: {len(schema_context)} chars)")

        # Step 3: Assess ambiguity (only for very short vague questions)
        if not conversation_context and len(effective_question.split()) <= 3:
            ambiguity = await llm.assess_ambiguity(effective_question, schema_context)
            if ambiguity.is_ambiguous:
                elapsed = (time.time() - start_time) * 1000
                return PipelineResult(
                    answer=ambiguity.clarifying_question or "Could you please be more specific?",
                    is_clarification=True,
                    domain=domain,
                    execution_time_ms=elapsed,
                )

        # Step 4-5: Generate SQL with retry loop
        last_sql = None
        last_error = None
        all_attempts = []

        log.info("Step 3: Starting SQL generation with retry loop (max 3 attempts)...")
        for attempt in range(1, MAX_SQL_RETRIES + 1):
            sql, results, error = await _generate_and_execute_sql(
                llm=llm,
                question=effective_question,
                schema_context=schema_context,
                attempt=attempt,
                previous_sql=last_sql,
                previous_error=last_error,
            )

            all_attempts.append({"sql": sql, "error": error, "row_count": len(results) if results else 0})

            # Success with results
            if results is not None and len(results) > 0:
                elapsed = (time.time() - start_time) * 1000
                log.info(f"Step 3 ✓ SUCCESS | Found {len(results)} rows in {elapsed:.0f}ms")
                log.info("=" * 80)
                return PipelineResult(
                    answer="",  # Filled by formatter
                    sql=sql,
                    domain=domain,
                    raw_results=results,
                    row_count=len(results),
                    execution_time_ms=elapsed,
                )

            # Query executed but returned 0 results
            if results is not None and len(results) == 0:
                if attempt < MAX_SQL_RETRIES:
                    last_sql = sql
                    last_error = (
                        "Query returned 0 results. The data might exist but your filters "
                        "are too strict. Try: removing semester/date filters, using ILIKE "
                        "for fuzzy matching, using LEFT JOINs, or querying the data with "
                        "fewer conditions to see what's available."
                    )
                    continue
                else:
                    # All retries exhausted with 0 results
                    elapsed = (time.time() - start_time) * 1000
                    return PipelineResult(
                        answer="",
                        sql=sql,
                        domain=domain,
                        raw_results=[],
                        row_count=0,
                        execution_time_ms=elapsed,
                    )

            # Query had an execution error
            if error:
                if attempt < MAX_SQL_RETRIES:
                    last_sql = sql
                    last_error = error
                    continue
                else:
                    # All retries exhausted with errors
                    elapsed = (time.time() - start_time) * 1000
                    answer = await llm.generate_response(
                        effective_question, sql, [], error=error
                    )
                    return PipelineResult(
                        answer=answer,
                        sql=sql,
                        domain=domain,
                        error=error,
                        execution_time_ms=elapsed,
                    )

        # Should not reach here, but just in case
        elapsed = (time.time() - start_time) * 1000
        return PipelineResult(
            answer="I couldn't find the data you're looking for after multiple attempts. Try rephrasing your question.",
            sql=last_sql,
            domain=domain,
            raw_results=[],
            row_count=0,
            execution_time_ms=elapsed,
        )

    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        log.error(f"PIPELINE ERROR | {type(e).__name__}: {e}", exc_info=True)
        log.info("=" * 80)
        return PipelineResult(
            answer="I encountered an error processing your question. Please try again.",
            error=str(e),
            execution_time_ms=elapsed,
        )
