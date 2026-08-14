"""Smart response formatter - formats raw query results into user-friendly responses."""

import re
from typing import Optional

from tabulate import tabulate

from app.core.models import PipelineResult
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_provider


# No artificial row cap - display all results returned by the query
MAX_TABLE_ROWS = None


def _snake_to_title(name: str) -> str:
    """Convert snake_case or raw column names to Title Case."""
    # Handle common abbreviations
    name = name.replace("_id", " ID").replace("_lpa", " (LPA)")
    # Split on underscores and capitalize
    parts = name.replace("_", " ").split()
    return " ".join(word.capitalize() for word in parts)


def _is_single_value_result(results: list[dict]) -> bool:
    """Check if result is a single aggregate value (COUNT, AVG, SUM, etc.)."""
    if len(results) != 1:
        return False
    row = results[0]
    # Must be a single column that looks like an aggregate
    if len(row) != 1:
        return False
    # Check if the column name suggests an aggregate
    key = list(row.keys())[0].lower()
    aggregate_indicators = ["count", "avg", "sum", "min", "max", "total", "average"]
    return any(ind in key for ind in aggregate_indicators)



def _format_table(results: list[dict], max_rows: int | None = MAX_TABLE_ROWS) -> str:
    """Format results as a markdown table."""
    if not results:
        return ""

    # Get headers
    headers = [_snake_to_title(col) for col in results[0].keys()]
    raw_headers = list(results[0].keys())

    # Truncate only if a max is explicitly set
    truncated = False
    total_count = len(results)
    if max_rows is not None and total_count > max_rows:
        display_results = results[:max_rows]
        truncated = True
    else:
        display_results = results

    # Build rows
    rows = []
    for row in display_results:
        formatted_row = []
        for key in raw_headers:
            val = row[key]
            # Format numbers nicely
            if isinstance(val, float):
                if val == int(val):
                    formatted_row.append(str(int(val)))
                else:
                    formatted_row.append(f"{val:.2f}")
            elif val is None:
                formatted_row.append("-")
            else:
                formatted_row.append(str(val))
        rows.append(formatted_row)

    table = tabulate(rows, headers=headers, tablefmt="pipe")

    if truncated:
        table += f"\n\n*Showing first {max_rows} of {total_count} results.*"

    return table


def format_results_basic(results: list[dict], question: str) -> str:
    """
    Format results without LLM assistance (fallback).

    Uses heuristics to determine the best format:
    - Single value: plain text sentence
    - Multi-row: markdown table
    - Empty: friendly message
    """
    if not results:
        return "No results found for your query. Try broadening your search or rephrasing your question."

    if _is_single_value_result(results):
        row = results[0]
        values = list(row.values())
        keys = list(row.keys())

        if len(values) == 1:
            key_name = _snake_to_title(keys[0])
            return f"**{key_name}:** {values[0]}"
        else:
            parts = []
            for k, v in row.items():
                parts.append(f"**{_snake_to_title(k)}:** {v}")
            return " | ".join(parts)

    # Multi-row result
    count = len(results)
    summary = f"Found **{count}** result{'s' if count > 1 else ''}:\n\n"
    table = _format_table(results)
    return summary + table


async def format_response(
    pipeline_result: PipelineResult,
    question: str,
    provider: Optional[BaseLLMProvider] = None,
) -> str:
    """
    Format the pipeline result into a user-friendly response.

    For single-value results or errors, uses the LLM for natural language.
    For multi-row results, uses table formatting with a brief LLM summary.

    Args:
        pipeline_result: The result from the pipeline
        question: Original user question
        provider: LLM provider (uses default if None)

    Returns:
        Formatted response string
    """
    # If already has an answer (error case or clarification), return it
    if pipeline_result.answer and not pipeline_result.raw_results:
        return pipeline_result.answer

    results = pipeline_result.raw_results or []
    sql = pipeline_result.sql or ""

    # No results
    if not results:
        return (
            "I couldn't find any matching data. This might mean:\n"
            "- The specific record doesn't exist in the database\n"
            "- The filters were too specific\n\n"
            "Try rephrasing with fewer constraints or asking what data is available."
        )

    # Try to get LLM-generated natural language summary
    llm = provider or get_provider()

    try:
        if _is_single_value_result(results):
            # For true aggregates (COUNT, AVG, etc.), let LLM create a natural sentence
            response = await llm.generate_response(question, sql, results)
            return response
        else:
            # For multi-row results, only return a brief intro sentence.
            # The frontend renders the actual data table from rawData.
            try:
                summary = await llm.generate_response(question, sql, results)
                summary_clean = summary.strip()
                # Only use summary if it's short and doesn't contain actual data values
                if len(summary_clean) < 200 and "|" not in summary_clean and "@" not in summary_clean:
                    return summary_clean
            except Exception:
                pass
            # Fallback: generic intro
            count = len(results)
            return f"Found **{count}** result{'s' if count > 1 else ''}:"
    except Exception:
        # Fallback to basic formatting if LLM fails
        count = len(results)
        return f"Found **{count}** result{'s' if count > 1 else ''}:"
