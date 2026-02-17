"""
Agent orchestrator using OpenAI Assistants API.
Manages multiple assistants and routes tasks appropriately.
"""
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.agents.assistant_agent import AssistantAgent
from app.config.openrouter import get_llm_client, get_llm_config


class AgentOrchestrator:
    """
    Orchestrates multiple OpenAI Assistants for complex browser automation.
    Routes commands to appropriate assistants based on capabilities.
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.client = get_llm_client()
        self.config = get_llm_config()

        # Assistant cache: assistant_id -> AssistantAgent
        self._assistants: Dict[str, AssistantAgent] = {}

    async def get_or_create_assistant(
        self,
        assistant_id: str,
        name: str,
        instructions: str,
        capabilities: List[str],
    ) -> AssistantAgent:
        """
        Get or create an assistant agent.

        Args:
            assistant_id: Database assistant ID
            name: Assistant name
            instructions: Custom instructions
            capabilities: List of capability names

        Returns:
            AssistantAgent instance
        """
        if assistant_id in self._assistants:
            return self._assistants[assistant_id]

        # Create new assistant agent
        agent = AssistantAgent(
            name=name,
            instructions=instructions,
            capabilities=capabilities,
        )

        self._assistants[assistant_id] = agent
        return agent

    async def execute_command(
        self,
        command: str,
        assistant_id: str,
        session_id: str,
        assistant_name: str,
        instructions: str,
        capabilities: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a command using the specified assistant.

        Args:
            command: User command
            assistant_id: Database assistant ID
            session_id: Session ID
            assistant_name: Assistant name
            instructions: Assistant instructions
            capabilities: Available capabilities
            conversation_history: Previous messages
            context: Additional context

        Returns:
            Execution result
        """
        try:
            # Get or create assistant
            agent = await self.get_or_create_assistant(
                assistant_id=assistant_id,
                name=assistant_name,
                instructions=instructions,
                capabilities=capabilities,
            )

            # Execute command
            result = await agent.execute_command(
                command=command,
                session_id=session_id,
                conversation_history=conversation_history,
            )

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
        assistant_id: str,
        session_id: str,
        assistant_name: str,
        instructions: str,
        capabilities: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream command execution with real-time updates.

        Args:
            command: User command
            assistant_id: Database assistant ID
            session_id: Session ID
            assistant_name: Assistant name
            instructions: Assistant instructions
            capabilities: Available capabilities
            conversation_history: Previous messages
            context: Additional context

        Yields:
            Execution progress chunks
        """
        try:
            # Get or create assistant
            agent = await self.get_or_create_assistant(
                assistant_id=assistant_id,
                name=assistant_name,
                instructions=instructions,
                capabilities=capabilities,
            )

            # Stream command execution
            async for chunk in agent.stream_command(
                command=command,
                session_id=session_id,
                conversation_history=conversation_history,
            ):
                yield chunk

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    async def update_assistant_capabilities(
        self, assistant_id: str, capabilities: List[str]
    ):
        """
        Update capabilities for an assistant.

        Args:
            assistant_id: Database assistant ID
            capabilities: New capability list
        """
        if assistant_id in self._assistants:
            agent = self._assistants[assistant_id]
            await agent.update_capabilities(capabilities)

    def remove_assistant(self, assistant_id: str):
        """
        Remove assistant from cache.

        Args:
            assistant_id: Database assistant ID
        """
        if assistant_id in self._assistants:
            del self._assistants[assistant_id]

    def get_assistant_count(self) -> int:
        """Get number of cached assistants."""
        return len(self._assistants)


# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """
    Get or create the global orchestrator instance.

    Returns:
        AgentOrchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()

    return _orchestrator
