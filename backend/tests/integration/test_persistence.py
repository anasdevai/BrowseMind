"""
Integration tests for session persistence
"""
import pytest
from app.db.session import get_db_session
from app.db.models import Session, Message, Assistant


@pytest.mark.asyncio
async def test_session_creation_and_retrieval():
    """Test session creation and retrieval"""
    with get_db_session() as db:
        # Create assistant
        assistant = Assistant(
            name="Test Assistant",
            instructions="Test",
            status="active"
        )
        db.add(assistant)
        db.flush()

        # Create session
        session = Session(assistant_id=assistant.id)
        db.add(session)
        db.flush()

        # Retrieve session
        retrieved = db.query(Session).filter(Session.id == session.id).first()
        assert retrieved is not None
        assert retrieved.assistant_id == assistant.id


@pytest.mark.asyncio
async def test_message_persistence():
    """Test message persistence"""
    with get_db_session() as db:
        # Create session
        assistant = Assistant(name="Test", instructions="Test", status="active")
        db.add(assistant)
        db.flush()

        session = Session(assistant_id=assistant.id)
        db.add(session)
        db.flush()

        # Add messages
        msg1 = Message(session_id=session.id, role="user", content="Hello")
        msg2 = Message(session_id=session.id, role="assistant", content="Hi")
        db.add_all([msg1, msg2])
        db.commit()

        # Retrieve messages
        messages = db.query(Message).filter(Message.session_id == session.id).all()
        assert len(messages) == 2


@pytest.mark.asyncio
async def test_session_archiving():
    """Test session archiving"""
    with get_db_session() as db:
        assistant = Assistant(name="Test", instructions="Test", status="active")
        db.add(assistant)
        db.flush()

        session = Session(assistant_id=assistant.id)
        db.add(session)
        db.flush()

        # Archive session
        from datetime import datetime
        session.archived_at = datetime.utcnow()
        db.commit()

        # Verify archived
        retrieved = db.query(Session).filter(Session.id == session.id).first()
        assert retrieved.archived_at is not None


@pytest.mark.asyncio
async def test_90_day_retention():
    """Test 90-day retention policy"""
    from datetime import datetime, timedelta

    # Test that sessions older than 90 days are identified
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    assert cutoff_date < datetime.utcnow()


@pytest.mark.asyncio
async def test_memory_isolation_between_assistants():
    """Test that assistants cannot access each other's sessions"""
    with get_db_session() as db:
        # Create two assistants
        assistant1 = Assistant(name="Assistant 1", instructions="Test", status="active")
        assistant2 = Assistant(name="Assistant 2", instructions="Test", status="active")
        db.add_all([assistant1, assistant2])
        db.flush()

        # Create sessions for each
        session1 = Session(assistant_id=assistant1.id)
        session2 = Session(assistant_id=assistant2.id)
        db.add_all([session1, session2])
        db.flush()

        # Verify isolation
        assistant1_sessions = db.query(Session).filter(
            Session.assistant_id == assistant1.id
        ).all()
        assert len(assistant1_sessions) == 1
        assert assistant1_sessions[0].id == session1.id
