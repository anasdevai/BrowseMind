"""
Tool permission validator.
Enforces capability restrictions per assistant (FR-006, FR-016).
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models import Assistant, AssistantCapability, Capability


class PermissionValidator:
    """
    Validates tool permissions for assistants.
    Ensures assistants can only use explicitly granted capabilities.
    """

    def __init__(self, db: Session):
        self.db = db

    def validate_tool_permission(
        self,
        assistant_id: str,
        tool_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if an assistant has permission to use a tool.

        Args:
            assistant_id: Assistant UUID
            tool_name: Tool/capability name

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        # Get assistant
        assistant = self.db.query(Assistant).filter(
            Assistant.id == assistant_id
        ).first()

        if not assistant:
            return False, f"Assistant {assistant_id} not found"

        if assistant.status != "active":
            return False, f"Assistant {assistant_id} is not active"

        # Get capability
        capability = self.db.query(Capability).filter(
            Capability.name == tool_name
        ).first()

        if not capability:
            return False, f"Tool {tool_name} not found"

        if not capability.enabled:
            return False, f"Tool {tool_name} is disabled"

        # Check if assistant has this capability
        has_capability = self.db.query(AssistantCapability).filter(
            AssistantCapability.assistant_id == assistant_id,
            AssistantCapability.capability_id == capability.id
        ).first()

        if not has_capability:
            return False, f"Assistant does not have permission to use {tool_name}"

        return True, None

    def get_assistant_capabilities(self, assistant_id: str) -> List[str]:
        """
        Get list of capability names for an assistant.

        Args:
            assistant_id: Assistant UUID

        Returns:
            List of capability names
        """
        capabilities = (
            self.db.query(Capability)
            .join(AssistantCapability)
            .filter(AssistantCapability.assistant_id == assistant_id)
            .filter(Capability.enabled == True)
            .all()
        )

        return [cap.name for cap in capabilities]

    def validate_capability_count(
        self,
        assistant_id: str,
        new_capabilities: List[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that adding capabilities won't exceed max limit (10).

        Args:
            assistant_id: Assistant UUID
            new_capabilities: List of capability names to add

        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        # Get current capability count
        current_count = self.db.query(AssistantCapability).filter(
            AssistantCapability.assistant_id == assistant_id
        ).count()

        total_count = current_count + len(new_capabilities)

        if total_count > 10:
            return False, f"Cannot exceed 10 capabilities per assistant (current: {current_count}, adding: {len(new_capabilities)})"

        return True, None

    def can_add_capability(
        self,
        assistant_id: str,
        capability_name: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a capability can be added to an assistant.

        Args:
            assistant_id: Assistant UUID
            capability_name: Capability name to add

        Returns:
            Tuple of (can_add: bool, error_message: Optional[str])
        """
        # Check capability exists
        capability = self.db.query(Capability).filter(
            Capability.name == capability_name
        ).first()

        if not capability:
            return False, f"Capability {capability_name} not found"

        if not capability.enabled:
            return False, f"Capability {capability_name} is disabled"

        # Check if already has capability
        has_capability = self.db.query(AssistantCapability).filter(
            AssistantCapability.assistant_id == assistant_id,
            AssistantCapability.capability_id == capability.id
        ).first()

        if has_capability:
            return False, f"Assistant already has capability {capability_name}"

        # Check count limit
        current_count = self.db.query(AssistantCapability).filter(
            AssistantCapability.assistant_id == assistant_id
        ).count()

        if current_count >= 10:
            return False, f"Assistant already has maximum 10 capabilities"

        return True, None


def validate_tool_permission(
    db: Session,
    assistant_id: str,
    tool_name: str
) -> tuple[bool, Optional[str]]:
    """
    Convenience function for validating tool permissions.

    Args:
        db: Database session
        assistant_id: Assistant UUID
        tool_name: Tool name

    Returns:
        Tuple of (allowed: bool, error_message: Optional[str])
    """
    validator = PermissionValidator(db)
    return validator.validate_tool_permission(assistant_id, tool_name)
