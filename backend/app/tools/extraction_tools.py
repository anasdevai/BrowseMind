"""
Content extraction tools for retrieving data from web pages.
These tools send execution requests to the extension via WebSocket.
"""
from typing import Any, Dict

from app.tools.base import Tool, register_tool


@register_tool
class ExtractTextTool(Tool):
    """Extract text content from page elements."""

    name = "extract_text"
    display_name = "Extract Text"
    description = "Extract text content from page elements"
    category = "extraction"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for elements to extract text from"
                },
                "all": {
                    "type": "boolean",
                    "description": "Extract from all matching elements (vs first only)",
                    "default": False
                },
                "trim": {
                    "type": "boolean",
                    "description": "Trim whitespace from extracted text",
                    "default": True
                }
            },
            "required": ["selector"]
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text extraction."""
        self.validate_params(params)

        return {
            "tool": self.name,
            "params": {
                "selector": params["selector"],
                "all": params.get("all", False),
                "trim": params.get("trim", True)
            }
        }


@register_tool
class ExtractLinksTool(Tool):
    """Extract all links from the page or a specific section."""

    name = "extract_links"
    display_name = "Extract Links"
    description = "Extract all links from the page or a specific section"
    category = "extraction"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector to limit link extraction (optional)"
                },
                "filter_pattern": {
                    "type": "string",
                    "description": "Regex pattern to filter URLs (optional)"
                }
            }
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute link extraction."""
        return {
            "tool": self.name,
            "params": {
                "selector": params.get("selector"),
                "filter_pattern": params.get("filter_pattern")
            }
        }


@register_tool
class ExtractTablesTool(Tool):
    """Extract table data from the page."""

    name = "extract_tables"
    display_name = "Extract Tables"
    description = "Extract table data from the page"
    category = "extraction"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for specific table (optional)"
                },
                "include_headers": {
                    "type": "boolean",
                    "description": "Include table headers in output",
                    "default": True
                }
            }
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute table extraction."""
        return {
            "tool": self.name,
            "params": {
                "selector": params.get("selector"),
                "include_headers": params.get("include_headers", True)
            }
        }


@register_tool
class GetDOMTool(Tool):
    """Get the DOM structure of the page or element."""

    name = "get_dom"
    display_name = "Get DOM Structure"
    description = "Get the DOM structure of the page or element"
    category = "extraction"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for specific element (optional)"
                },
                "depth": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum depth to traverse",
                    "default": 3
                }
            }
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute DOM extraction."""
        return {
            "tool": self.name,
            "params": {
                "selector": params.get("selector"),
                "depth": params.get("depth", 3)
            }
        }


@register_tool
class HighlightElementTool(Tool):
    """Visually highlight an element on the page."""

    name = "highlight_element"
    display_name = "Highlight Element"
    description = "Visually highlight an element on the page"
    category = "utility"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for element to highlight"
                },
                "duration_ms": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10000,
                    "description": "Highlight duration in milliseconds",
                    "default": 2000
                }
            },
            "required": ["selector"]
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute element highlighting."""
        self.validate_params(params)

        return {
            "tool": self.name,
            "params": {
                "selector": params["selector"],
                "duration_ms": params.get("duration_ms", 2000)
            }
        }
