"""
WebSocket error handling and protocol versioning.
Provides error codes, validation, and protocol version management.
"""
from enum import Enum
from typing import Any, Dict, Optional


# Protocol version
PROTOCOL_VERSION = "1.0.0"


class ErrorCode(Enum):
    """Standard error codes for WebSocket protocol."""

    # Connection errors
    INVALID_FORMAT = "INVALID_FORMAT"
    MISSING_TYPE = "MISSING_TYPE"
    MISSING_ID = "MISSING_ID"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"
    PROTOCOL_VERSION_MISMATCH = "PROTOCOL_VERSION_MISMATCH"

    # Authentication errors
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_EXTENSION_ID = "INVALID_EXTENSION_ID"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Command errors
    ASSISTANT_NOT_FOUND = "ASSISTANT_NOT_FOUND"
    ASSISTANT_INACTIVE = "ASSISTANT_INACTIVE"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    QUEUE_FULL = "QUEUE_FULL"
    INVALID_TEXT = "INVALID_TEXT"
    COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"

    # Assistant management errors
    MAX_ASSISTANTS_REACHED = "MAX_ASSISTANTS_REACHED"
    ASSISTANT_NAME_EXISTS = "ASSISTANT_NAME_EXISTS"
    INVALID_ASSISTANT_NAME = "INVALID_ASSISTANT_NAME"
    INVALID_INSTRUCTIONS = "INVALID_INSTRUCTIONS"
    MAX_CAPABILITIES_REACHED = "MAX_CAPABILITIES_REACHED"
    CAPABILITY_NOT_FOUND = "CAPABILITY_NOT_FOUND"

    # Tool execution errors
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    INVALID_TOOL_PARAMS = "INVALID_TOOL_PARAMS"
    TOOL_EXECUTION_FAILED = "TOOL_EXECUTION_FAILED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # Internal errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


class ProtocolError(Exception):
    """
    Exception for protocol-level errors.
    Includes error code and optional details.
    """

    def __init__(self, code: ErrorCode, message: str, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code.value,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        return result


class MessageValidator:
    """
    Validates WebSocket messages against protocol specification.
    """

    @staticmethod
    def validate_message_structure(message: dict) -> None:
        """
        Validate basic message structure.

        Args:
            message: Message dictionary

        Raises:
            ProtocolError: If validation fails
        """
        if not isinstance(message, dict):
            raise ProtocolError(
                ErrorCode.INVALID_FORMAT,
                "Message must be a JSON object"
            )

        if "type" not in message:
            raise ProtocolError(
                ErrorCode.MISSING_TYPE,
                "Message must include 'type' field"
            )

        if "id" not in message:
            raise ProtocolError(
                ErrorCode.MISSING_ID,
                "Message must include 'id' field"
            )

        if "timestamp" not in message:
            raise ProtocolError(
                ErrorCode.INVALID_FORMAT,
                "Message must include 'timestamp' field"
            )

    @staticmethod
    def validate_command(payload: dict) -> None:
        """
        Validate command message payload.

        Args:
            payload: Command payload

        Raises:
            ProtocolError: If validation fails
        """
        if not isinstance(payload, dict):
            raise ProtocolError(
                ErrorCode.INVALID_FORMAT,
                "Command payload must be an object"
            )

        # Validate text
        text = payload.get("text")
        if not text or not isinstance(text, str):
            raise ProtocolError(
                ErrorCode.INVALID_TEXT,
                "Command text is required and must be a string"
            )

        if len(text) < 1 or len(text) > 10000:
            raise ProtocolError(
                ErrorCode.INVALID_TEXT,
                "Command text must be 1-10,000 characters",
                {"length": len(text)}
            )

        # Validate assistant_id
        assistant_id = payload.get("assistant_id")
        if not assistant_id or not isinstance(assistant_id, str):
            raise ProtocolError(
                ErrorCode.INVALID_FORMAT,
                "assistant_id is required and must be a string"
            )

    @staticmethod
    def validate_create_assistant(payload: dict) -> None:
        """
        Validate create_assistant message payload.

        Args:
            payload: Create assistant payload

        Raises:
            ProtocolError: If validation fails
        """
        if not isinstance(payload, dict):
            raise ProtocolError(
                ErrorCode.INVALID_FORMAT,
                "Create assistant payload must be an object"
            )

        # Validate name
        name = payload.get("name")
        if not name or not isinstance(name, str):
            raise ProtocolError(
                ErrorCode.INVALID_ASSISTANT_NAME,
                "Assistant name is required and must be a string"
            )

        if len(name) < 1 or len(name) > 100:
            raise ProtocolError(
                ErrorCode.INVALID_ASSISTANT_NAME,
                "Assistant name must be 1-100 characters",
                {"length": len(name)}
            )

        # Validate instructions
        instructions = payload.get("instructions")
        if not instructions or not isinstance(instructions, str):
            raise ProtocolError(
                ErrorCode.INVALID_INSTRUCTIONS,
                "Instructions are required and must be a string"
            )

        if len(instructions) < 10 or len(instructions) > 10000:
            raise ProtocolError(
                ErrorCode.INVALID_INSTRUCTIONS,
                "Instructions must be 10-10,000 characters",
                {"length": len(instructions)}
            )

        # Validate capabilities
        capabilities = payload.get("capabilities", [])
        if not isinstance(capabilities, list):
            raise ProtocolError(
                ErrorCode.INVALID_FORMAT,
                "Capabilities must be an array"
            )

        if len(capabilities) > 10:
            raise ProtocolError(
                ErrorCode.MAX_CAPABILITIES_REACHED,
                "Maximum 10 capabilities per assistant",
                {"count": len(capabilities)}
            )


def check_protocol_version(client_version: Optional[str]) -> bool:
    """
    Check if client protocol version is compatible.

    Args:
        client_version: Client protocol version string

    Returns:
        True if compatible, False otherwise
    """
    if not client_version:
        return True  # Allow connections without version (assume compatible)

    # For now, only exact match required
    # Future: implement semantic versioning compatibility
    return client_version == PROTOCOL_VERSION


def get_protocol_info() -> dict:
    """
    Get protocol information for handshake.

    Returns:
        Dictionary with protocol details
    """
    return {
        "version": PROTOCOL_VERSION,
        "supported_message_types": [
            # Client → Server
            "command",
            "tool_result",
            "cancel_command",
            "list_assistants",
            "create_assistant",
            "activate_assistant",
            "deactivate_assistant",
            "delete_assistant",
            "get_queue_status",
            "archive_session",
            "ping",
            # Server → Client
            "tool_execution",
            "status_update",
            "queue_status",
            "assistant_list",
            "assistant_created",
            "assistant_updated",
            "error",
            "ack",
            "pong"
        ],
        "rate_limit": {
            "max_messages": 100,
            "window_seconds": 60
        },
        "timeouts": {
            "command_timeout_seconds": 30,
            "heartbeat_interval_seconds": 30
        }
    }
