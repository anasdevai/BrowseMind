"""
Session management utilities for conversation persistence.
Handles session creation, retrieval, and lifecycle management.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Assistant, Message, Session as DBSession


class SessionManager:
    """
    Manages conversation sessions and message persistence.
    Handles session lifecycle, retrieval, and archiving.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        assistant_id: str,
        title: Optional[str] = None
    ) -> DBSession:
        """
        Create a new conversation session.

        Args:
            assistant_id: Assistant UUID
            title: Optional session title

        Returns:
            Created session object
        """
        session = DBSession(
            assistant_id=assistant_id,
            title=title or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[DBSession]:
        """
        Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Session object or None if not found
        """
        return self.db.query(DBSession).filter(
            DBSession.id == session_id,
            DBSession.archived_at.is_(None)
        ).first()

    def get_or_create_session(
        self,
        assistant_id: str,
        session_id: Optional[str] = None
    ) -> DBSession:
        """
        Get existing session or create new one.

        Args:
            assistant_id: Assistant UUID
            session_id: Optional existing session ID

        Returns:
            Session object
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session

        # Create new session
        return self.create_session(assistant_id)

    def list_sessions(
        self,
        assistant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        include_archived: bool = False
    ) -> List[DBSession]:
        """
        List sessions with pagination.

        Args:
            assistant_id: Optional filter by assistant
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            include_archived: Include archived sessions

        Returns:
            List of session objects
        """
        query = self.db.query(DBSession)

        if assistant_id:
            query = query.filter(DBSession.assistant_id == assistant_id)

        if not include_archived:
            query = query.filter(DBSession.archived_at.is_(None))

        return (
            query.order_by(DBSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_session_messages(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        Get messages for a session.

        Args:
            session_id: Session UUID
            limit: Maximum number of messages
            offset: Number of messages to skip

        Returns:
            List of message objects
        """
        return (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def archive_session(self, session_id: str) -> bool:
        """
        Archive a session.

        Args:
            session_id: Session UUID

        Returns:
            True if archived, False if not found
        """
        session = self.get_session(session_id)
        if not session:
            return False

        session.archived_at = datetime.utcnow()
        self.db.commit()
        return True

    def get_active_session(self, assistant_id: str) -> Optional[DBSession]:
        """
        Get the most recent active session for an assistant.

        Args:
            assistant_id: Assistant UUID

        Returns:
            Most recent session or None
        """
        return (
            self.db.query(DBSession)
            .filter(
                DBSession.assistant_id == assistant_id,
                DBSession.archived_at.is_(None)
            )
            .order_by(DBSession.updated_at.desc())
            .first()
        )

    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """
        Get session summary with metadata.

        Args:
            session_id: Session UUID

        Returns:
            Dictionary with session summary or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        message_count = (
            self.db.query(Message)
            .filter(Message.session_id == session_id)
            .count()
        )

        return {
            "id": session.id,
            "assistant_id": session.assistant_id,
            "title": session.title,
            "message_count": message_count,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "archived_at": session.archived_at.isoformat() if session.archived_at else None,
        }

    def find_expired_sessions(self, days: int = 90) -> List[DBSession]:
        """
        Find sessions older than specified days.

        Args:
            days: Number of days for expiration

        Returns:
            List of expired sessions
        """
        expiration_date = datetime.utcnow() - timedelta(days=days)

        return (
            self.db.query(DBSession)
            .filter(
                DBSession.updated_at < expiration_date,
                DBSession.archived_at.is_(None)
            )
            .all()
        )
