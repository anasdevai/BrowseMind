"""
Base tool class and registry for browser control capabilities.
Provides tool interface, validation, and registration system.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
import json

from app.db.models import Capability
from app.db.session import get_db_session


class Tool(ABC):
    """
    Abstract base class for all browser control tools.
    Each tool must implement execute() and define its schema.
    """

    # Tool metadata (must be defined by subclasses)
    name: str = ""
    display_name: str = ""
    description: str = ""
    category: str = ""
    risk_level: str = "low"

    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.

        Args:
            params: Tool-specific parameters

        Returns:
            Dictionary with execution result

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If execution fails
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get JSON Schema for tool parameters.

        Returns:
            JSON Schema dictionary
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate parameters against tool schema.

        Args:
            params: Parameters to validate

        Raises:
            ValueError: If validation fails
        """
        # Basic validation - subclasses can override for custom validation
        schema = self.get_schema()
        required = schema.get("required", [])

        for field in required:
            if field not in params:
                raise ValueError(f"Missing required parameter: {field}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool metadata to dictionary.

        Returns:
            Tool metadata dictionary
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "risk_level": self.risk_level,
            "schema": self.get_schema()
        }


class ToolRegistry:
    """
    Registry for managing available tools.
    Provides tool lookup, validation, and capability mapping.
    """

    def __init__(self):
        self._tools: Dict[str, Type[Tool]] = {}

    def register(self, tool_class: Type[Tool]) -> None:
        """
        Register a tool class.

        Args:
            tool_class: Tool class to register
        """
        if not tool_class.name:
            raise ValueError(f"Tool class {tool_class.__name__} must define 'name'")

        self._tools[tool_class.name] = tool_class
        print(f"Registered tool: {tool_class.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool instance by name.

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        tool_class = self._tools.get(name)
        if tool_class:
            return tool_class()
        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.

        Returns:
            List of tool metadata dictionaries
        """
        return [
            tool_class().to_dict()
            for tool_class in self._tools.values()
        ]

    def get_tool_names(self) -> List[str]:
        """
        Get list of registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def validate_capability(self, capability_name: str) -> bool:
        """
        Check if a capability name corresponds to a registered tool.

        Args:
            capability_name: Capability name to validate

        Returns:
            True if valid, False otherwise
        """
        return capability_name in self._tools

    async def get_capabilities_from_db(self) -> List[Capability]:
        """
        Load capabilities from database.

        Returns:
            List of Capability objects
        """
        with get_db_session() as db:
            capabilities = db.query(Capability).filter(Capability.enabled == True).all()
            return capabilities


# Global tool registry instance
_tool_registry: ToolRegistry = None


def get_tool_registry() -> ToolRegistry:
    """
    Get or create the global tool registry.

    Returns:
        ToolRegistry instance
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def register_tool(tool_class: Type[Tool]) -> Type[Tool]:
    """
    Decorator for registering tool classes.

    Args:
        tool_class: Tool class to register

    Returns:
        The same tool class (for chaining)

    Example:
        @register_tool
        class NavigateTool(Tool):
            name = "navigate"
            ...
    """
    registry = get_tool_registry()
    registry.register(tool_class)
    return tool_class
