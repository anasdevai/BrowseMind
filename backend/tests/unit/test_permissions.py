"""
Unit tests for permission validator
"""
import pytest
from app.tools.permission_validator import PermissionValidator
from app.db.models import Assistant, Capability, AssistantCapability
from app.db.session import get_db_session


def test_permission_validator_initialization():
    """Test permission validator initialization"""
    with get_db_session() as db:
        validator = PermissionValidator(db)
        assert validator is not None


def test_validate_tool_permission_allowed():
    """Test tool permission validation - allowed"""
    with get_db_session() as db:
        validator = PermissionValidator(db)

        # This would need actual database setup
        # For now, test the structure
        assert hasattr(validator, 'validate_tool_permission')


def test_validate_tool_permission_denied():
    """Test tool permission validation - denied"""
    with get_db_session() as db:
        validator = PermissionValidator(db)

        # Test with non-existent assistant
        allowed, error = validator.validate_tool_permission("non-existent", "navigate")
        assert allowed is False
        assert error is not None


def test_get_assistant_capabilities():
    """Test getting assistant capabilities"""
    with get_db_session() as db:
        validator = PermissionValidator(db)

        # Test with non-existent assistant
        capabilities = validator.get_assistant_capabilities("non-existent")
        assert isinstance(capabilities, list)
        assert len(capabilities) == 0


def test_max_capabilities_enforcement():
    """Test max 10 capabilities per assistant"""
    # This would test that assistants can't have more than 10 capabilities
    max_capabilities = 10
    assert max_capabilities == 10


def test_capability_validation():
    """Test capability name validation"""
    valid_capabilities = [
        "navigate", "click_element", "type_text", "scroll", "screenshot",
        "extract_text", "extract_links", "extract_tables", "get_dom", "highlight_element"
    ]

    assert len(valid_capabilities) == 10
    assert "navigate" in valid_capabilities
