"""
Main orchestrator agent for natural language browser control.
Parses user commands and coordinates tool execution.
"""
from typing import Any, AsyncGenerator, Dict, List

from app.agents.base_agent import BaseAgent


class MainAgent(BaseAgent):
    """
    Main agent for browser control orchestration.
    Interprets natural language commands and executes browser tools.
    """

    def __init__(self):
        """Initialize main agent with optimized settings."""
        super().__init__(
            model="gpt-4-turbo-preview",
            temperature=0.3,  # Lower temperature for more deterministic tool calling
            max_tokens=2000
        )

    def get_system_prompt(self) -> str:
        """
        Get system prompt for main agent.

        Returns:
            System prompt defining agent behavior
        """
        return """You are BrowserMind, an AI assistant that controls web browsers through natural language.

Your role is to:
1. Understand user commands about web browsing tasks
2. Break down complex tasks into tool calls
3. Execute browser control tools (navigate, click, type, extract data, etc.)
4. Provide clear feedback about actions taken
5. Handle errors gracefully and suggest alternatives

Guidelines:
- Be concise and action-oriented in responses
- Always confirm what action you're taking before executing
- If a command is ambiguous, ask for clarification
- Use CSS selectors for precise element targeting
- Extract and present data in a clear, structured format
- Report errors clearly and suggest fixes

Available capabilities:
- Navigate to URLs
- Click elements (by selector or text)
- Type text into input fields
- Extract text, links, and table data
- Scroll pages
- Take screenshots
- Get DOM structure
- Highlight elements for user reference

When executing tools:
- Validate parameters before calling
- Use appropriate wait conditions for navigation
- Handle multiple matching elements with index parameter
- Provide context about what data was extracted

Remember: You can only use tools that the assistant has been granted permission for.
"""

    async def process_command(
        self,
        command: str,
        conversation_history: List[Dict[str, str]],
        available_capabilities: List[str]
    ) -> Dict[str, Any]:
        """
        Process a user command and generate response with tool calls.

        Args:
            command: User command
            conversation_history: Previous messages
            available_capabilities: Capabilities assistant has access to

        Returns:
            Response with content and tool calls
        """
        return await self.process_message(
            message=command,
            conversation_history=conversation_history,
            available_capabilities=available_capabilities
        )

    async def stream_command(
        self,
        command: str,
        conversation_history: List[Dict[str, str]],
        available_capabilities: List[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user command with streaming response.

        Args:
            command: User command
            conversation_history: Previous messages
            available_capabilities: Capabilities assistant has access to

        Yields:
            Response chunks (text deltas and tool calls)
        """
        async for chunk in self.stream_message(
            message=command,
            conversation_history=conversation_history,
            available_capabilities=available_capabilities
        ):
            yield chunk

    async def process_tool_result(
        self,
        tool_name: str,
        tool_result: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        available_capabilities: List[str]
    ) -> Dict[str, Any]:
        """
        Process tool execution result and generate follow-up response.

        Args:
            tool_name: Name of executed tool
            tool_result: Tool execution result
            conversation_history: Previous messages
            available_capabilities: Capabilities assistant has access to

        Returns:
            Follow-up response
        """
        # Add tool result to conversation
        tool_message = {
            "role": "function",
            "name": tool_name,
            "content": str(tool_result)
        }

        # Get agent's interpretation of the result
        return await self.process_message(
            message="",  # Empty message, agent will respond to tool result
            conversation_history=conversation_history + [tool_message],
            available_capabilities=available_capabilities
        )
