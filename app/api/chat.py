"""Chat API endpoint - wires together pipeline, formatter, logger, and conversation state."""

from fastapi import APIRouter, HTTPException, Request

from app.core.chart_analyzer import analyze_chart_data
from app.core.conversation import conversation_manager
from app.core.logger import query_logger, QueryLogEntry
from app.core.models import ChatRequest, ChatResponse, ChartConfig, PipelineResult
from app.core.pipeline import run_pipeline
from app.core.rate_limiter import rate_limiter
from app.formatter.response_formatter import format_response

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - accepts a natural language question, returns a formatted answer.

    Flow:
    1. Validate input
    2. Rate limit check
    3. Check if this is a clarification follow-up
    4. Run the NL-to-SQL pipeline
    5. Format the response
    6. Log the query
    7. Return the response
    """
    question = request.question.strip()

    # Input validation
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if len(question) > 500:
        raise HTTPException(
            status_code=400,
            detail="Question is too long. Please keep it under 500 characters.",
        )

    # Get or create conversation
    conv = conversation_manager.get_or_create(request.conversation_id)

    # Rate limiting
    if not rate_limiter.is_allowed(conv.id):
        remaining = rate_limiter.get_remaining(conv.id)
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment before asking another question.",
        )

    # Check if this is a follow-up to a clarification
    clarification_context = conversation_manager.get_clarification_context(conv.id)

    # If not a clarification follow-up, check for conversation history context
    conversation_context = clarification_context
    if not conversation_context:
        # Get previous conversation context for follow-up questions
        conversation_context = conversation_manager.get_conversation_context(conv.id)

    # Run pipeline
    try:
        result: PipelineResult = await run_pipeline(
            question=question,
            conversation_context=conversation_context,
        )
    except Exception as e:
        # Log the error
        query_logger.log(QueryLogEntry(
            user_question=question,
            error=str(e),
            conversation_id=conv.id,
        ))
        return ChatResponse(
            answer="I'm having trouble processing your question right now. Please try again in a moment.",
            is_clarification=False,
            conversation_id=conv.id,
        )

    # Handle clarification case
    if result.is_clarification:
        conversation_manager.set_awaiting_clarification(
            conversation_id=conv.id,
            original_question=question,
            clarifying_question=result.answer,
            domain=result.domain,
        )

        # Log the clarification
        query_logger.log(QueryLogEntry(
            user_question=question,
            classified_domain=result.domain,
            is_clarification=True,
            execution_time_ms=result.execution_time_ms,
            conversation_id=conv.id,
        ))

        return ChatResponse(
            answer=result.answer,
            is_clarification=True,
            conversation_id=conv.id,
            domain=result.domain,
        )

    # Format the response
    try:
        formatted_answer = await format_response(result, question)
    except Exception:
        # Fallback if formatting fails
        from app.formatter.response_formatter import format_results_basic
        formatted_answer = format_results_basic(result.raw_results or [], question)

    # Log the query
    query_logger.log(QueryLogEntry(
        user_question=question,
        classified_domain=result.domain,
        generated_sql=result.sql,
        validation_passed=result.error is None,
        validation_error=result.error,
        execution_time_ms=result.execution_time_ms,
        row_count=result.row_count,
        conversation_id=conv.id,
    ))

    # Store last result for follow-up context
    conversation_manager.set_last_result(
        conversation_id=conv.id,
        question=question,
        sql=result.sql,
        answer=formatted_answer[:300],  # Store truncated answer
    )

    # Always send raw_results for download (CSV/XLSX), and analyze for charts
    raw_data_response = result.raw_results if result.raw_results else None
    suggested_chart = None
    chart_config_response = None

    if result.raw_results:
        chart_data = analyze_chart_data(result.raw_results)
        if chart_data:
            suggested_chart = chart_data["suggested_chart_type"]
            chart_config_response = ChartConfig(**chart_data["chart_config"])

    return ChatResponse(
        answer=formatted_answer,
        sql=result.sql,
        is_clarification=False,
        conversation_id=conv.id,
        domain=result.domain,
        row_count=result.row_count,
        raw_data=raw_data_response,
        suggested_chart_type=suggested_chart,
        chart_config=chart_config_response,
    )
