"""Pydantic models for request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    """Chat endpoint request body."""
    question: str = Field(..., min_length=1, max_length=500, description="User question in natural language")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for follow-up/clarification context")


class ChartConfig(BaseModel):
    """Chart configuration metadata."""
    x_key: str = Field(..., description="Column to use as x-axis")
    y_keys: list[str] = Field(..., description="Columns to use as y-axis values")
    title: Optional[str] = Field(None, description="Chart title")


class ChatResponse(BaseModel):
    """Chat endpoint response body."""
    answer: str = Field(..., description="Formatted response to the user")
    sql: Optional[str] = Field(None, description="Generated SQL query (for transparency)")
    is_clarification: bool = Field(False, description="Whether this is a clarifying question")
    conversation_id: str = Field(..., description="Conversation ID for follow-up")
    domain: Optional[str] = Field(None, description="Detected domain of the question")
    row_count: Optional[int] = Field(None, description="Number of result rows")
    raw_data: Optional[list[dict]] = Field(None, description="Raw query results for export and charting")
    suggested_chart_type: Optional[str] = Field(None, description="Suggested chart type: bar, line, pie, area")
    chart_config: Optional[ChartConfig] = Field(None, description="Chart axis and title configuration")


class PipelineResult(BaseModel):
    """Internal pipeline result."""
    answer: str
    sql: Optional[str] = None
    is_clarification: bool = False
    domain: Optional[str] = None
    raw_results: Optional[list] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None
