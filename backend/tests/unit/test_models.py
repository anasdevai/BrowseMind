"""
Unit tests for database models
"""
import pytest
from datetime import datetime
from app.db.models import Assistant, Session, Message, Capability, AssistantCapability, ToolLog


def test_assistant_creation():
    """Test assistant model creation"""
    assistant = Assistant(
        name="Test Assistant",
        instructions="Test instructions",
        status="active"
    )
    assert assistant.name == "Test Assistant"
    assert assistant.status == "active"
    assert assistant.deleted_at is None


def test_session_creation():
    """Test session model creation"""
    session = Session(
        assistant_id="test-id"
    )
    assert session.assistant_id == "test-id"
    assert session.archived_at is None


def test_message_creation():
    """Test message model creation"""
    message = Message(
        session_id="session-id",
        role="user",
        content="Test message"
    )
    assert message.role == "user"
    assert message.content == "Test message"


def test_capability_creation():
    """Test capability model creation"""
    capability = Capability(
        name="navigate",
        display_name="Navigate",
        description="Navigate to URLs",
        category="browser_control",
        risk_level="low",
        enabled=True
    )
    assert capability.name == "navigate"
    assert capability.enabled is True


def test_assistant_capability_association():
    """Test assistant-capability association"""
    assoc = AssistantCapability(
        assistant_id="assistant-id",
        capability_id="capability-id"
    )
    assert assoc.assistant_id == "assistant-id"
    assert assoc.capability_id == "capability-id"


def test_tool_log_creation():
    """Test tool log model creation"""
    log = ToolLog(
        session_id="session-id",
        tool_name="navigate",
        params='{"url": "https://example.com"}',
        result='{"success": true}',
        success=True,
        execution_time_ms=150
    )
    assert log.tool_name == "navigate"
    assert log.success is True
    assert log.execution_time_ms == 150
