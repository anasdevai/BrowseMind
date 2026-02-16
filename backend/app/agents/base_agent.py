"""
Base agent class with OpenAI SDK integration and tool calling.
Provides foundation for specialized agents with streaming support.
"""
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

import openai
from openai import AsyncOpenAI

from app.config import settings
from app.tools.base import get_tool_registry


class BaseAgent(ABC):
    """
    Abstract base class for AI agents.
    Handles OpenAI API integration, tool calling, and streaming responses.
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize base agent.

        Args:
            model: OpenAI model to use
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.tool_registry = get_tool_registry()

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.

        Returns:
            System prompt string
        """
        pass

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI function calling schema for available tools.

        Returns:
            List of tool schemas in OpenAI format
        """
        tools = []
        for tool_dict in self.tool_registry.list_tools():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_dict["name"],
                    "description": tool_dict["description"],
                    "parameters": tool_dict["schema"]
                }
            })
        return tools

    async def process_message(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        available_capabilities: List[str]
    ) -> Dict[str, Any]:
        """
        Process a user message and generate response with tool calls.

        Args:
            message: User message
            conversation_history: Previous messages in conversation
            available_capabilities: List of capability names assistant has access to

        Returns:
            Dictionary with response text and tool calls
        """
        # Filter tools to only those the assistant has permission for
        all_tools = self.get_available_tools()
        allowed_tools = [
            tool for tool in all_tools
            if tool["function"]["name"] in available_capabilities
        ]

        # Build messages
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})

        # Call OpenAI API
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=allowed_tools if allowed_tools else None,
                tool_choice="auto" if allowed_tools else None,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            message_obj = response.choices[0].message

            # Extract tool calls
            tool_calls = []
            if message_obj.tool_calls:
                for tool_call in message_obj.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    })

            return {
                "content": message_obj.content or "",
                "tool_calls": tool_calls,
                "finish_reason": response.choices[0].finish_reason
            }

        except openai.APIError as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    async def stream_message(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        available_capabilities: List[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a user message with streaming response.

        Args:
            message: User message
            conversation_history: Previous messages in conversation
            available_capabilities: List of capability names assistant has access to

        Yields:
            Chunks of response data (text deltas and tool calls)
        """
        # Filter tools to only those the assistant has permission for
        all_tools = self.get_available_tools()
        allowed_tools = [
            tool for tool in all_tools
            if tool["function"]["name"] in available_capabilities
        ]

        # Build messages
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": message})

        # Call OpenAI API with streaming
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=allowed_tools if allowed_tools else None,
                tool_choice="auto" if allowed_tools else None,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta

                # Text content
                if delta.content:
                    yield {
                        "type": "content",
                        "content": delta.content
                    }

                # Tool calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        yield {
                            "type": "tool_call",
                            "id": tool_call.id,
                            "name": tool_call.function.name if tool_call.function else None,
                            "arguments": tool_call.function.arguments if tool_call.function else None
                        }

                # Finish reason
                if chunk.choices[0].finish_reason:
                    yield {
                        "type": "finish",
                        "reason": chunk.choices[0].finish_reason
                    }

        except openai.APIError as e:
            yield {
                "type": "error",
                "error": f"OpenAI API error: {e}"
            }

    async def execute_tool(
        self,
        tool_name: str,
        tool_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool with given parameters.

        Args:
            tool_name: Name of tool to execute
            tool_params: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or parameters invalid
            RuntimeError: If tool execution fails
        """
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        return await tool.execute(tool_params)
