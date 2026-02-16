"""
Assistant registry for managing and loading assistants dynamically.
Provides metadata and capability information for assistants.
"""
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.models import Assistant, AssistantCapability, Capability


class AssistantRegistry:
    """
    Registry for managing assistants and their capabilities.
    Provides lookup and validation for assistant operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_assistant(self, assistant_id: str) -> Optional[Assistant]:
        """
        Get assistant by ID.

        Args:
            assistant_id: Assistant UUID

        Returns:
            Assistant object or None if not found
        """
        return self.db.query(Assistant).filter(
            Assistant.id == assistant_id,
            Assistant.deleted_at.is_(None)
        ).first()

    def get_active_assistant(self) -> Optional[Assistant]:
        """
        Get the currently active assistant.

        Returns:
            Active assistant or None if no assistant is active
        """
        return self.db.query(Assistant).filter(
            Assistant.status == "active",
            Assistant.deleted_at.is_(None)
        ).first()

    def list_assistants(self, include_inactive: bool = True) -> List[Assistant]:
        """
        List all assistants.

        Args:
            include_inactive: Include inactive assistants

        Returns:
            List of Assistant objects
        """
        query = self.db.query(Assistant).filter(
            Assistant.deleted_at.is_(None)
        )

        if not include_inactive:
            query = query.filter(Assistant.status == "active")

        return query.all()

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
            .filter(
                AssistantCapability.assistant_id == assistant_id,
                Capability.enabled == True
            )
            .all()
        )

        return [cap.name for cap in capabilities]

    def get_assistant_metadata(self, assistant_id: str) -> Optional[Dict]:
        """
        Get assistant metadata including capabilities.

        Args:
            assistant_id: Assistant UUID

        Returns:
            Dictionary with assistant metadata or None if not found
        """
        assistant = self.get_assistant(assistant_id)
        if not assistant:
            return None

        capabilities = self.get_assistant_capabilities(assistant_id)

        return {
            "id": assistant.id,
            "name": assistant.name,
            "instructions": assistant.instructions,
            "status": assistant.status,
            "capabilities": capabilities,
            "capability_count": len(capabilities),
            "created_at": assistant.created_at.isoformat(),
            "updated_at": assistant.updated_at.isoformat(),
        }

    def validate_assistant_active(self, assistant_id: str) -> tuple[bool, Optional[str]]:
        """
        Validate that an assistant exists and is active.

        Args:
            assistant_id: Assistant UUID

        Returns:
            Tuple of (valid: bool, error_message: Optional[str])
        """
        assistant = self.get_assistant(assistant_id)

        if not assistant:
            return False, f"Assistant {assistant_id} not found"

        if assistant.status != "active":
            return False, f"Assistant {assistant_id} is not active"

        return True, None

    def count_assistants(self) -> int:
        """
        Count total number of assistants (excluding deleted).

        Returns:
            Number of assistants
        """
        return self.db.query(Assistant).filter(
            Assistant.deleted_at.is_(None)
        ).count()

    def can_create_assistant(self) -> tuple[bool, Optional[str]]:
        """
        Check if a new assistant can be created (max 20).

        Returns:
            Tuple of (can_create: bool, error_message: Optional[str])
        """
        count = self.count_assistants()

        if count >= 20:
            return False, f"Maximum 20 assistants allowed (current: {count})"

        return True, None
