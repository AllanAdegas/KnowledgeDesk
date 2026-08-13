"""Chat session and message persistence (SQLite via SQLAlchemy async ORM).

A "turn" is modeled here as a single stored message (either role). The
sliding window described in specs/chatbot.spec.md ("últimos 10 turnos") is
implemented as "last `max_history_turns` messages", configured in
`core.config.settings.max_history_turns` — never hardcoded.
"""

import uuid
from datetime import UTC, datetime
from typing import TypedDict

from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from core.config import settings
from core.database import AsyncSessionEngine, Base, get_engine_holder


class ChatSessionModel(Base):
    """A conversation session."""

    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class ChatMessageModel(Base):
    """A single message within a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))


class HistoryMessage(TypedDict):
    """A message as returned by `get_history`, ready for the LLM context."""

    role: str
    content: str


async def create_session(engine_holder: AsyncSessionEngine | None = None) -> str:
    """Create a new chat session and return its UUID."""
    holder = engine_holder or get_engine_holder()
    await holder.init_models()

    session_id = str(uuid.uuid4())
    async with holder.session_factory() as db_session:
        db_session.add(ChatSessionModel(id=session_id))
        await db_session.commit()

    return session_id


async def add_message(
    session_id: str,
    role: str,
    content: str,
    engine_holder: AsyncSessionEngine | None = None,
) -> None:
    """Append a message to a session's history."""
    holder = engine_holder or get_engine_holder()
    await holder.init_models()

    async with holder.session_factory() as db_session:
        db_session.add(ChatMessageModel(session_id=session_id, role=role, content=content))
        await db_session.commit()


async def get_history(
    session_id: str,
    limit: int | None = None,
    engine_holder: AsyncSessionEngine | None = None,
) -> list[HistoryMessage]:
    """Return the most recent `limit` messages for a session, oldest first.

    Defaults to `settings.max_history_turns` when `limit` is not given.
    """
    holder = engine_holder or get_engine_holder()
    await holder.init_models()
    window = limit if limit is not None else settings.max_history_turns

    async with holder.session_factory() as db_session:
        statement = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.id.desc())
            .limit(window)
        )
        result = await db_session.execute(statement)
        rows = list(result.scalars().all())

    rows.reverse()
    return [{"role": row.role, "content": row.content} for row in rows]
