"""
Tool initialization module.
Imports all tool modules to trigger @register_tool decorators.
"""
# Import all tool modules to register them
from app.tools import browser_tools, extraction_tools

__all__ = ["browser_tools", "extraction_tools"]
