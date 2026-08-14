"""Conversation state management for clarification flows."""

import uuid
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationState:
    """State for a single conversation session."""
    id: str
    original_question: Optional[str] = None
    clarifying_question: Optional[str] = None
    domain: Optional[str] = None
    last_question: Optional[str] = None
    last_sql: Optional[str] = None
    last_answer: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    is_awaiting_clarification: bool = False


class ConversationManager:
    """
    In-memory conversation state manager.

    Tracks conversations for clarification follow-ups.
    Conversations expire after 10 minutes of inactivity.
    """

    EXPIRY_SECONDS = 600  # 10 minutes

    def __init__(self):
        self._conversations: dict[str, ConversationState] = {}

    def create_conversation(self) -> ConversationState:
        """Create a new conversation."""
        conv_id = str(uuid.uuid4())
        state = ConversationState(id=conv_id)
        self._conversations[conv_id] = state
        return state

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get an existing conversation, or None if not found/expired."""
        state = self._conversations.get(conversation_id)
        if state is None:
            return None

        # Check expiry
        if time.time() - state.last_active > self.EXPIRY_SECONDS:
            del self._conversations[conversation_id]
            return None

        state.last_active = time.time()
        return state

    def get_or_create(self, conversation_id: Optional[str]) -> ConversationState:
        """Get existing conversation or create a new one."""
        if conversation_id:
            state = self.get_conversation(conversation_id)
            if state:
                return state
        return self.create_conversation()

    def set_awaiting_clarification(
        self,
        conversation_id: str,
        original_question: str,
        clarifying_question: str,
        domain: Optional[str] = None,
    ) -> None:
        """Mark a conversation as awaiting clarification."""
        state = self._conversations.get(conversation_id)
        if state:
            state.original_question = original_question
            state.clarifying_question = clarifying_question
            state.domain = domain
            state.is_awaiting_clarification = True

    def get_clarification_context(self, conversation_id: str) -> Optional[str]:
        """
        Get the context string for a clarification follow-up.

        Returns a combined string of original question + clarifying question,
        or None if the conversation isn't in clarification state.
        """
        state = self._conversations.get(conversation_id)
        if state and state.is_awaiting_clarification:
            # Clear the clarification state
            state.is_awaiting_clarification = False
            context = (
                f"Original question: {state.original_question}\n"
                f"Clarification asked: {state.clarifying_question}"
            )
            return context
        return None

    def set_last_result(
        self,
        conversation_id: str,
        question: str,
        sql: Optional[str],
        answer: str,
    ) -> None:
        """Store the last successful query result for follow-up context."""
        state = self._conversations.get(conversation_id)
        if state:
            state.last_question = question
            state.last_sql = sql
            state.last_answer = answer

    def get_conversation_context(self, conversation_id: str) -> Optional[str]:
        """
        Get conversation history context for follow-up questions.

        Returns a string describing what was previously asked/answered.
        """
        state = self._conversations.get(conversation_id)
        if state and state.last_question:
            context = f"Previous question: {state.last_question}\n"
            if state.last_sql:
                context += f"Previous SQL used: {state.last_sql}\n"
            if state.last_answer:
                # Truncate long answers
                answer_preview = state.last_answer[:200]
                context += f"Previous answer: {answer_preview}\n"
            return context
        return None

    def clear_expired(self) -> int:
        """Remove expired conversations. Returns count removed."""
        now = time.time()
        expired = [
            cid for cid, state in self._conversations.items()
            if now - state.last_active > self.EXPIRY_SECONDS
        ]
        for cid in expired:
            del self._conversations[cid]
        return len(expired)


# Singleton instance
conversation_manager = ConversationManager()
