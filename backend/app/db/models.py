"""
SQLAlchemy database models for BrowserMind platform.
Implements all 6 core entities with encryption support for sensitive fields.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    event,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Assistant(Base):
    """
    Specialized AI helper with specific capabilities and isolated memory.
    """

    __tablename__ = "assistants"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    instructions = Column(Text, nullable=False)  # Encrypted
    model = Column(String(50), nullable=False, default="gpt-4-turbo-preview")
    status = Column(
        String(20),
        nullable=False,
        default="inactive",
        server_default="inactive",
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=True)
    meta_data = Column("metadata", Text, nullable=True)  # Encrypted JSON

    # Relationships
    sessions = relationship("Session", back_populates="assistant", cascade="all, delete-orphan")
    capabilities = relationship("AssistantCapability", back_populates="assistant", cascade="all, delete-orphan")
    tool_logs = relationship("ToolLog", back_populates="assistant", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'inactive', 'deleted')", name="check_status"),
        CheckConstraint("length(name) BETWEEN 1 AND 100", name="check_name_length"),
        CheckConstraint("length(instructions) >= 10", name="check_instructions_length"),
        Index("idx_assistants_status_active", "status", "last_active_at"),
    )


class Session(Base):
    """
    Continuous interaction period between user and assistant.
    """

    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    archived = Column(Boolean, nullable=False, default=False, server_default="0")
    expires_at = Column(DateTime, nullable=False)
    meta_data = Column("metadata", Text, nullable=True)  # Encrypted JSON

    # Relationships
    assistant = relationship("Assistant", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    tool_logs = relationship("ToolLog", back_populates="session")

    # Constraints
    __table_args__ = (
        CheckConstraint("last_active_at >= created_at", name="check_valid_dates"),
        Index("idx_sessions_assistant", "assistant_id", "last_active_at"),
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_archived_expires", "archived", "expires_at"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(days=90)


class Message(Base):
    """
    Single message in a conversation (user, assistant, or system).
    """

    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)  # Encrypted
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    token_count = Column(Integer, nullable=True)
    meta_data = Column("metadata", Text, nullable=True)  # Encrypted JSON

    # Relationships
    session = relationship("Session", back_populates="messages")

    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="check_role"),
        CheckConstraint("length(content) BETWEEN 1 AND 100000", name="check_content_length"),
        Index("idx_messages_session", "session_id", "timestamp"),
        Index("idx_messages_timestamp", "timestamp"),
    )


class Capability(Base):
    """
    Specific action an assistant can perform (tool permission).
    """

    __tablename__ = "capabilities"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(20), nullable=False)
    risk_level = Column(String(10), nullable=False)
    schema = Column(Text, nullable=False)  # JSON Schema
    enabled = Column(Boolean, nullable=False, default=True, server_default="1")

    # Relationships
    assistants = relationship("AssistantCapability", back_populates="capability")
    tool_logs = relationship("ToolLog", back_populates="capability")

    # Constraints
    __table_args__ = (
        CheckConstraint("category IN ('navigation', 'interaction', 'extraction', 'utility')", name="check_category"),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name="check_risk_level"),
        Index("idx_capabilities_category", "category", "enabled"),
    )


class AssistantCapability(Base):
    """
    Join table mapping assistants to their allowed capabilities.
    """

    __tablename__ = "assistant_capabilities"

    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), primary_key=True)
    capability_id = Column(String, ForeignKey("capabilities.id", ondelete="RESTRICT"), primary_key=True)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    assistant = relationship("Assistant", back_populates="capabilities")
    capability = relationship("Capability", back_populates="assistants")

    # Constraints
    __table_args__ = (Index("idx_assistant_capabilities_capability", "capability_id"),)


class ToolLog(Base):
    """
    Audit log of all tool executions for debugging and compliance.
    """

    __tablename__ = "tool_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    assistant_id = Column(String, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(String, ForeignKey("capabilities.id", ondelete="RESTRICT"), nullable=False)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    input_params = Column(Text, nullable=False)  # JSON
    output_result = Column(Text, nullable=True)  # JSON
    status = Column(String(20), nullable=False)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    assistant = relationship("Assistant", back_populates="tool_logs")
    capability = relationship("Capability", back_populates="tool_logs")
    session = relationship("Session", back_populates="tool_logs")

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('success', 'error', 'timeout', 'cancelled')", name="check_status"),
        CheckConstraint("execution_time_ms >= 0", name="check_execution_time"),
        Index("idx_tool_logs_assistant", "assistant_id", "timestamp"),
        Index("idx_tool_logs_capability", "capability_id", "timestamp"),
        Index("idx_tool_logs_session", "session_id", "timestamp"),
        Index("idx_tool_logs_timestamp", "timestamp"),
        Index("idx_tool_logs_status", "status", "timestamp"),
    )
