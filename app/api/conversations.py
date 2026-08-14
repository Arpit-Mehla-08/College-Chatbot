"""Conversation persistence API - CRUD for chat history."""

import json
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

router = APIRouter()

# Separate DB for conversations (doesn't pollute the data DB)
_conv_engine: AsyncEngine | None = None

CONV_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "conversations.db")


def get_conv_engine() -> AsyncEngine:
    """Get or create the conversations database engine."""
    global _conv_engine
    if _conv_engine is None:
        _conv_engine = create_async_engine(
            f"sqlite+aiosqlite:///{CONV_DB_PATH}",
            connect_args={"check_same_thread": False},
        )
    return _conv_engine


async def init_conversations_db():
    """Initialize the conversations database schema."""
    engine = get_conv_engine()
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sql_query TEXT,
                raw_data TEXT,
                chart_type TEXT,
                chart_config TEXT,
                domain TEXT,
                row_count INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)
        """))


# Pydantic models for the API
class MessageCreate(BaseModel):
    """Message to save."""
    id: str
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str
    sql_query: Optional[str] = None
    raw_data: Optional[list[dict]] = None
    chart_type: Optional[str] = None
    chart_config: Optional[dict] = None
    domain: Optional[str] = None
    row_count: Optional[int] = None
    created_at: Optional[str] = None


class ConversationCreate(BaseModel):
    """Create/save a conversation."""
    id: str
    title: str = ""
    messages: list[MessageCreate] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Update a conversation (add messages)."""
    title: Optional[str] = None
    messages: list[MessageCreate] = []


class MessageResponse(BaseModel):
    """Message in API response."""
    id: str
    role: str
    content: str
    sql_query: Optional[str] = None
    raw_data: Optional[list[dict]] = None
    chart_type: Optional[str] = None
    chart_config: Optional[dict] = None
    domain: Optional[str] = None
    row_count: Optional[int] = None
    created_at: str


class ConversationResponse(BaseModel):
    """Full conversation response."""
    id: str
    title: str
    messages: list[MessageResponse] = []
    created_at: str
    updated_at: str


class ConversationListItem(BaseModel):
    """Conversation in list response (without messages)."""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0


class ConversationListResponse(BaseModel):
    """Paginated conversation list."""
    conversations: list[ConversationListItem]
    total: int
    page: int
    page_size: int


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """List all conversations, ordered by most recent."""
    await init_conversations_db()
    engine = get_conv_engine()

    async with engine.connect() as conn:
        # Get total count
        result = await conn.execute(text("SELECT COUNT(*) FROM conversations"))
        total = result.scalar() or 0

        # Get paginated conversations
        offset = (page - 1) * page_size
        result = await conn.execute(text("""
            SELECT c.id, c.title, c.created_at, c.updated_at,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as message_count
            FROM conversations c
            ORDER BY c.updated_at DESC
            LIMIT :limit OFFSET :offset
        """), {"limit": page_size, "offset": offset})

        rows = result.fetchall()
        conversations = [
            ConversationListItem(
                id=row[0],
                title=row[1],
                created_at=row[2],
                updated_at=row[3],
                message_count=row[4],
            )
            for row in rows
        ]

    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a full conversation with all messages."""
    await init_conversations_db()
    engine = get_conv_engine()

    async with engine.connect() as conn:
        # Get conversation
        result = await conn.execute(
            text("SELECT id, title, created_at, updated_at FROM conversations WHERE id = :id"),
            {"id": conversation_id},
        )
        conv_row = result.fetchone()
        if not conv_row:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        result = await conn.execute(
            text("""
                SELECT id, role, content, sql_query, raw_data, chart_type, chart_config, domain, row_count, created_at
                FROM messages
                WHERE conversation_id = :conv_id
                ORDER BY created_at ASC
            """),
            {"conv_id": conversation_id},
        )
        msg_rows = result.fetchall()

        messages = []
        for row in msg_rows:
            raw_data = None
            chart_config = None
            if row[4]:
                try:
                    raw_data = json.loads(row[4])
                except (json.JSONDecodeError, TypeError):
                    pass
            if row[6]:
                try:
                    chart_config = json.loads(row[6])
                except (json.JSONDecodeError, TypeError):
                    pass

            messages.append(MessageResponse(
                id=row[0],
                role=row[1],
                content=row[2],
                sql_query=row[3],
                raw_data=raw_data,
                chart_type=row[5],
                chart_config=chart_config,
                domain=row[7],
                row_count=row[8],
                created_at=row[9],
            ))

    return ConversationResponse(
        id=conv_row[0],
        title=conv_row[1],
        messages=messages,
        created_at=conv_row[2],
        updated_at=conv_row[3],
    )


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(body: ConversationCreate):
    """Create or save a full conversation."""
    await init_conversations_db()
    engine = get_conv_engine()

    now = datetime.utcnow().isoformat()
    created_at = body.created_at or now
    updated_at = body.updated_at or now

    async with engine.begin() as conn:
        # Upsert conversation
        await conn.execute(text("""
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES (:id, :title, :created_at, :updated_at)
            ON CONFLICT(id) DO UPDATE SET title = :title, updated_at = :updated_at
        """), {
            "id": body.id,
            "title": body.title,
            "created_at": created_at,
            "updated_at": updated_at,
        })

        # Insert messages
        for msg in body.messages:
            msg_created = msg.created_at or now
            raw_data_json = json.dumps(msg.raw_data) if msg.raw_data else None
            chart_config_json = json.dumps(msg.chart_config) if msg.chart_config else None

            await conn.execute(text("""
                INSERT OR IGNORE INTO messages
                    (id, conversation_id, role, content, sql_query, raw_data, chart_type, chart_config, domain, row_count, created_at)
                VALUES
                    (:id, :conv_id, :role, :content, :sql_query, :raw_data, :chart_type, :chart_config, :domain, :row_count, :created_at)
            """), {
                "id": msg.id,
                "conv_id": body.id,
                "role": msg.role,
                "content": msg.content,
                "sql_query": msg.sql_query,
                "raw_data": raw_data_json,
                "chart_type": msg.chart_type,
                "chart_config": chart_config_json,
                "domain": msg.domain,
                "row_count": msg.row_count,
                "created_at": msg_created,
            })

    # Return the created conversation
    return await get_conversation(body.id)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: str, body: ConversationUpdate):
    """Update a conversation - add new messages or update title."""
    await init_conversations_db()
    engine = get_conv_engine()

    now = datetime.utcnow().isoformat()

    async with engine.begin() as conn:
        # Check exists
        result = await conn.execute(
            text("SELECT id FROM conversations WHERE id = :id"),
            {"id": conversation_id},
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update title if provided
        if body.title is not None:
            await conn.execute(
                text("UPDATE conversations SET title = :title, updated_at = :now WHERE id = :id"),
                {"title": body.title, "now": now, "id": conversation_id},
            )
        else:
            await conn.execute(
                text("UPDATE conversations SET updated_at = :now WHERE id = :id"),
                {"now": now, "id": conversation_id},
            )

        # Add new messages
        for msg in body.messages:
            msg_created = msg.created_at or now
            raw_data_json = json.dumps(msg.raw_data) if msg.raw_data else None
            chart_config_json = json.dumps(msg.chart_config) if msg.chart_config else None

            await conn.execute(text("""
                INSERT OR IGNORE INTO messages
                    (id, conversation_id, role, content, sql_query, raw_data, chart_type, chart_config, domain, row_count, created_at)
                VALUES
                    (:id, :conv_id, :role, :content, :sql_query, :raw_data, :chart_type, :chart_config, :domain, :row_count, :created_at)
            """), {
                "id": msg.id,
                "conv_id": conversation_id,
                "role": msg.role,
                "content": msg.content,
                "sql_query": msg.sql_query,
                "raw_data": raw_data_json,
                "chart_type": msg.chart_type,
                "chart_config": chart_config_json,
                "domain": msg.domain,
                "row_count": msg.row_count,
                "created_at": msg_created,
            })

    return await get_conversation(conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    await init_conversations_db()
    engine = get_conv_engine()

    async with engine.begin() as conn:
        # Check exists
        result = await conn.execute(
            text("SELECT id FROM conversations WHERE id = :id"),
            {"id": conversation_id},
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Delete messages first, then conversation
        await conn.execute(
            text("DELETE FROM messages WHERE conversation_id = :id"),
            {"id": conversation_id},
        )
        await conn.execute(
            text("DELETE FROM conversations WHERE id = :id"),
            {"id": conversation_id},
        )

    return None
