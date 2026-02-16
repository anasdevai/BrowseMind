"""
Browser control tools for navigation and interaction.
These tools send execution requests to the extension via WebSocket.
"""
from typing import Any, Dict

from app.tools.base import Tool, register_tool


@register_tool
class NavigateTool(Tool):
    """Navigate the browser to a specified URL."""

    name = "navigate"
    display_name = "Navigate to URL"
    description = "Navigate the browser to a specified URL"
    category = "navigation"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "format": "uri",
                    "description": "URL to navigate to"
                },
                "wait_until": {
                    "type": "string",
                    "enum": ["load", "domcontentloaded", "networkidle"],
                    "description": "When to consider navigation complete",
                    "default": "load"
                },
                "timeout_ms": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 30000,
                    "description": "Navigation timeout in milliseconds",
                    "default": 30000
                }
            },
            "required": ["url"]
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute navigation.
        Note: Actual execution happens in the extension content script.
        This method validates parameters and returns the execution request.
        """
        self.validate_params(params)

        return {
            "tool": self.name,
            "params": {
                "url": params["url"],
                "wait_until": params.get("wait_until", "load"),
                "timeout_ms": params.get("timeout_ms", 30000)
            }
        }


@register_tool
class ClickElementTool(Tool):
    """Click on a page element by selector or text."""

    name = "click_element"
    display_name = "Click Element"
    description = "Click on a page element by selector or text"
    category = "interaction"
    risk_level = "medium"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the element"
                },
                "text": {
                    "type": "string",
                    "description": "Text content to match (alternative to selector)"
                },
                "index": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Index if multiple elements match",
                    "default": 0
                },
                "wait_for_navigation": {
                    "type": "boolean",
                    "description": "Wait for navigation after click",
                    "default": False
                }
            }
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute element click."""
        # Must have either selector or text
        if "selector" not in params and "text" not in params:
            raise ValueError("Must provide either 'selector' or 'text' parameter")

        return {
            "tool": self.name,
            "params": {
                "selector": params.get("selector"),
                "text": params.get("text"),
                "index": params.get("index", 0),
                "wait_for_navigation": params.get("wait_for_navigation", False)
            }
        }


@register_tool
class TypeTextTool(Tool):
    """Type text into an input field."""

    name = "type_text"
    display_name = "Type Text"
    description = "Type text into an input field"
    category = "interaction"
    risk_level = "medium"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for the input field"
                },
                "text": {
                    "type": "string",
                    "description": "Text to type"
                },
                "clear_first": {
                    "type": "boolean",
                    "description": "Clear existing text before typing",
                    "default": True
                },
                "press_enter": {
                    "type": "boolean",
                    "description": "Press Enter after typing",
                    "default": False
                }
            },
            "required": ["selector", "text"]
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text typing."""
        self.validate_params(params)

        return {
            "tool": self.name,
            "params": {
                "selector": params["selector"],
                "text": params["text"],
                "clear_first": params.get("clear_first", True),
                "press_enter": params.get("press_enter", False)
            }
        }


@register_tool
class ScrollTool(Tool):
    """Scroll the page in a specified direction."""

    name = "scroll"
    display_name = "Scroll Page"
    description = "Scroll the page in a specified direction"
    category = "navigation"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "top", "bottom"],
                    "description": "Scroll direction"
                },
                "amount": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Scroll amount in pixels (for up/down)",
                    "default": 500
                },
                "smooth": {
                    "type": "boolean",
                    "description": "Use smooth scrolling",
                    "default": True
                }
            },
            "required": ["direction"]
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scrolling."""
        self.validate_params(params)

        return {
            "tool": self.name,
            "params": {
                "direction": params["direction"],
                "amount": params.get("amount", 500),
                "smooth": params.get("smooth", True)
            }
        }


@register_tool
class ScreenshotTool(Tool):
    """Capture a screenshot of the page or element."""

    name = "screenshot"
    display_name = "Take Screenshot"
    description = "Capture a screenshot of the page or element"
    category = "utility"
    risk_level = "low"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector for specific element (optional)"
                },
                "full_page": {
                    "type": "boolean",
                    "description": "Capture full page screenshot",
                    "default": False
                },
                "format": {
                    "type": "string",
                    "enum": ["png", "jpeg"],
                    "description": "Image format",
                    "default": "png"
                }
            }
        }

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute screenshot capture."""
        return {
            "tool": self.name,
            "params": {
                "selector": params.get("selector"),
                "full_page": params.get("full_page", False),
                "format": params.get("format", "png")
            }
        }
