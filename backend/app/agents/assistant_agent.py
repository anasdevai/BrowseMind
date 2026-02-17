"""
OpenAI Assistants API-based agent system for BrowserMind.
Uses OpenAI's official Agent SDK (Assistants API) for production-ready agents.
"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.beta import Assistant, Thread
from openai.types.beta.threads import Run, Message

from app.config.openrouter import get_llm_client, get_llm_config, get_model_name
from app.tools.base import get_tool_registry


class AssistantAgent:
    """
    OpenAI Assistant-based agent for browser control.
    Uses Assistants API with function calling for tool execution.
    """

    def __init__(
        self,
        assistant_id: Optional[str] = None,
        name: str = "BrowserAgent",
        instructions: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
    ):
        """
        Initialize assistant agent.

        Args:
            assistant_id: Existing assistant ID (if resuming)
            name: Assistant name
            instructions: Custom instructions
            capabilities: List of capability names
        """
        self.client = get_llm_client()
        self.config = get_llm_config()
        self.assistant_id = assistant_id
        self.name = name
        self.capabilities = capabilities or []
        self.instructions = instructions or self._get_default_instructions()

        # Assistant and thread will be created on demand
        self._assistant: Optional[Assistant] = None
        self._threads: Dict[str, Thread] = {}  # session_id -> Thread

    def _get_default_instructions(self) -> str:
        """Get default assistant instructions."""
        return """You are BrowserMind, an AI assistant that controls web browsers through natural language.

Your role is to:
1. Understand user commands about web browsing tasks
2. Execute browser control tools (navigate, click, type, extract data, etc.)
3. Provide clear feedback about actions taken
4. Handle errors gracefully and suggest alternatives

Guidelines:
- Be concise and action-oriented
- Always confirm what action you're taking
- Use CSS selectors for precise element targeting
- Extract and present data clearly
- Report errors with helpful suggestions

When using tools:
- Validate parameters before calling
- Handle multiple matching elements appropriately
- Provide context about extracted data
- Confirm successful execution

You can ONLY use tools that match your granted capabilities."""

    async def _ensure_assistant(self) -> Assistant:
        """Ensure assistant exists, create if needed."""
        if self._assistant:
            return self._assistant

        if self.assistant_id:
            # Retrieve existing assistant
            self._assistant = await self.client.beta.assistants.retrieve(
                assistant_id=self.assistant_id
            )
        else:
            # Create new assistant with tools
            tools = self._build_tools()

            self._assistant = await self.client.beta.assistants.create(
                name=self.name,
                instructions=self.instructions,
                model=get_model_name(self.config),
                tools=tools,
            )
            self.assistant_id = self._assistant.id

        return self._assistant

    def _build_tools(self) -> List[Dict[str, Any]]:
        """Build OpenAI function tools from capabilities."""
        registry = get_tool_registry()
        tools = []

        for capability_name in self.capabilities:
            tool = registry.get_tool(capability_name)
            if tool:
                # Convert to OpenAI function format
                function_def = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.get_schema(),
                    },
                }
                tools.append(function_def)

        return tools

    async def _get_or_create_thread(self, session_id: str) -> Thread:
        """Get or create thread for session."""
        if session_id in self._threads:
            return self._threads[session_id]

        thread = await self.client.beta.threads.create()
        self._threads[session_id] = thread
        return thread

    async def execute_command(
        self,
        command: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a command using the assistant.

        Args:
            command: User command
            session_id: Session identifier
            conversation_history: Previous messages (optional, thread maintains history)

        Returns:
            Execution result with content and tool calls
        """
        try:
            # Ensure assistant exists
            assistant = await self._ensure_assistant()

            # Get or create thread
            thread = await self._get_or_create_thread(session_id)

            # Add user message to thread
            await self.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=command
            )

            # Create and execute run
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

            # Wait for completion and handle tool calls
            result = await self._wait_for_run_completion(thread.id, run.id)

            return result

        except Exception as e:
            return {
                "content": f"Error executing command: {str(e)}",
                "tool_calls": [],
                "finish_reason": "error",
                "success": False,
                "error": str(e),
            }

    async def stream_command(
        self,
        command: str,
        session_id: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream command execution with real-time updates.

        Args:
            command: User command
            session_id: Session identifier
            conversation_history: Previous messages

        Yields:
            Chunks of execution progress
        """
        try:
            # Ensure assistant exists
            assistant = await self._ensure_assistant()

            # Get or create thread
            thread = await self._get_or_create_thread(session_id)

            # Add user message
            await self.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=command
            )

            # Create streaming run
            async with self.client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=assistant.id,
            ) as stream:
                async for event in stream:
                    # Handle different event types
                    if event.event == "thread.message.delta":
                        # Text content delta
                        delta = event.data.delta
                        if delta.content:
                            for content in delta.content:
                                if content.type == "text":
                                    yield {
                                        "type": "content",
                                        "content": content.text.value,
                                    }

                    elif event.event == "thread.run.requires_action":
                        # Tool calls required
                        run = event.data
                        if run.required_action:
                            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                                yield {
                                    "type": "tool_call",
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments,
                                    "tool_call_id": tool_call.id,
                                }

                    elif event.event == "thread.run.completed":
                        yield {"type": "finish", "reason": "stop"}

                    elif event.event == "thread.run.failed":
                        yield {
                            "type": "error",
                            "error": event.data.last_error.message
                            if event.data.last_error
                            else "Unknown error",
                        }

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    async def _wait_for_run_completion(
        self, thread_id: str, run_id: str, max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for run completion and handle tool calls.

        Args:
            thread_id: Thread ID
            run_id: Run ID
            max_iterations: Maximum tool call iterations

        Returns:
            Final result
        """
        iterations = 0

        while iterations < max_iterations:
            # Get run status
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run_id
            )

            if run.status == "completed":
                # Get messages
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread_id, order="desc", limit=1
                )

                if messages.data:
                    message = messages.data[0]
                    content = ""
                    for block in message.content:
                        if block.type == "text":
                            content += block.text.value

                    return {
                        "content": content,
                        "tool_calls": [],
                        "finish_reason": "stop",
                        "success": True,
                    }

            elif run.status == "requires_action":
                # Handle tool calls
                tool_outputs = []
                if run.required_action:
                    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                        # Execute tool (will be handled by extension)
                        # For now, return tool call info
                        tool_outputs.append(
                            {
                                "tool_call_id": tool_call.id,
                                "output": json.dumps(
                                    {
                                        "status": "pending",
                                        "message": "Tool execution delegated to extension",
                                    }
                                ),
                            }
                        )

                # Submit tool outputs
                await self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id, run_id=run_id, tool_outputs=tool_outputs
                )

            elif run.status in ["failed", "cancelled", "expired"]:
                return {
                    "content": f"Run {run.status}: {run.last_error.message if run.last_error else 'Unknown error'}",
                    "tool_calls": [],
                    "finish_reason": "error",
                    "success": False,
                    "error": run.last_error.message if run.last_error else "Unknown error",
                }

            iterations += 1
            await asyncio.sleep(0.5)  # Poll interval

        return {
            "content": "Run exceeded maximum iterations",
            "tool_calls": [],
            "finish_reason": "error",
            "success": False,
            "error": "Maximum iterations exceeded",
        }

    async def update_capabilities(self, capabilities: List[str]):
        """Update assistant capabilities."""
        self.capabilities = capabilities

        if self._assistant:
            # Update assistant tools
            tools = self._build_tools()
            self._assistant = await self.client.beta.assistants.update(
                assistant_id=self.assistant_id, tools=tools
            )


import asyncio
