"""
Agent orchestrator for managing multiple Swarm agents.
Routes tasks to appropriate specialist agents and coordinates execution.
"""
import asyncio
from typing import Any, Dict, List, Optional

from swarm import Agent, Swarm
from swarm.types import Response

from app.agents.swarm_agents import BrowserAgent, SpecialistAgent
from app.config.openrouter import get_llm_client, get_llm_config, get_model_name


class AgentOrchestrator:
    """
    Orchestrates multiple Swarm agents for complex browser automation tasks.
    Routes commands to appropriate specialist agents based on task type.
    """

    def __init__(self):
        """Initialize orchestrator with specialist agents."""
        self.swarm = Swarm(client=get_llm_client())
        self.config = get_llm_config()

        # Create specialist agents
        self.navigation_agent = self._create_navigation_agent()
        self.extraction_agent = self._create_extraction_agent()
        self.interaction_agent = self._create_interaction_agent()

        # Create main coordinator agent
        self.coordinator = self._create_coordinator_agent()

        # Agent registry
        self.agents = {
            "coordinator": self.coordinator,
            "navigation": self.navigation_agent,
            "extraction": self.extraction_agent,
            "interaction": self.interaction_agent,
        }

    def _create_navigation_agent(self) -> Agent:
        """Create navigation specialist agent."""
        return Agent(
            name="NavigationAgent",
            model=get_model_name(self.config),
            instructions="""You are a navigation specialist for web browsing.

Your expertise:
- Navigate to URLs efficiently
- Handle page loading and wait conditions
- Scroll pages to find content
- Take screenshots for documentation

When given a navigation task:
1. Use the navigate tool with appropriate wait conditions
2. Verify page loaded successfully
3. Report the final URL and page status
4. Use scroll tool if content is not visible

Always confirm successful navigation before completing.""",
            functions=[],  # Tools will be added dynamically based on capabilities
        )

    def _create_extraction_agent(self) -> Agent:
        """Create data extraction specialist agent."""
        return Agent(
            name="ExtractionAgent",
            model=get_model_name(self.config),
            instructions="""You are a data extraction specialist for web pages.

Your expertise:
- Extract text content from elements
- Extract links and URLs
- Extract table data
- Get DOM structure
- Highlight elements for user reference

When given an extraction task:
1. Identify the best selector for target elements
2. Use appropriate extraction tool (text, links, tables, DOM)
3. Format extracted data clearly
4. Handle multiple matches appropriately
5. Report if elements are not found

Always provide structured, clean data output.""",
            functions=[],
        )

    def _create_interaction_agent(self) -> Agent:
        """Create interaction specialist agent."""
        return Agent(
            name="InteractionAgent",
            model=get_model_name(self.config),
            instructions="""You are an interaction specialist for web automation.

Your expertise:
- Click buttons, links, and elements
- Type text into input fields
- Fill out forms
- Handle interactive elements

When given an interaction task:
1. Identify target elements using selectors or text
2. Verify elements are visible and clickable
3. Execute interactions in the correct order
4. Handle form submissions carefully
5. Report success or failure clearly

Always confirm element visibility before interaction.""",
            functions=[],
        )

    def _create_coordinator_agent(self) -> Agent:
        """Create main coordinator agent."""

        def transfer_to_navigation():
            """Transfer to navigation specialist for URL navigation and scrolling."""
            return self.navigation_agent

        def transfer_to_extraction():
            """Transfer to extraction specialist for data extraction tasks."""
            return self.extraction_agent

        def transfer_to_interaction():
            """Transfer to interaction specialist for clicking and typing."""
            return self.interaction_agent

        return Agent(
            name="Coordinator",
            model=get_model_name(self.config),
            instructions="""You are the main coordinator for BrowserMind.

Your role is to:
1. Understand user commands
2. Break down complex tasks into subtasks
3. Route subtasks to appropriate specialist agents
4. Coordinate multi-step workflows
5. Synthesize results from specialists

Task routing guidelines:
- Navigation tasks (go to URL, scroll) → NavigationAgent
- Extraction tasks (get text, extract links, get data) → ExtractionAgent
- Interaction tasks (click, type, fill form) → InteractionAgent

For complex tasks:
1. Break into sequential steps
2. Route each step to appropriate specialist
3. Pass context between specialists
4. Synthesize final result

Always provide clear, actionable responses to the user.""",
            functions=[transfer_to_navigation, transfer_to_extraction, transfer_to_interaction],
        )

    async def execute_command(
        self,
        command: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        capabilities: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a command using the orchestrator.

        Args:
            command: User command
            conversation_history: Previous messages
            capabilities: Available capabilities
            context: Additional context variables

        Returns:
            Execution result with content and metadata
        """
        # Build message history
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": command})

        # Add capabilities to context
        context_vars = context or {}
        context_vars["capabilities"] = capabilities or []

        try:
            # Run orchestrator
            response = self.swarm.run(
                agent=self.coordinator,
                messages=messages,
                context_variables=context_vars,
                model_override=get_model_name(self.config),
                max_turns=15,  # Allow multiple agent handoffs
                debug=False,
            )

            # Extract result
            result = {
                "content": self._extract_content(response),
                "tool_calls": self._extract_tool_calls(response),
                "agent_path": self._extract_agent_path(response),
                "finish_reason": "stop",
                "success": True,
            }

            return result

        except Exception as e:
            return {
                "content": f"Error executing command: {str(e)}",
                "tool_calls": [],
                "agent_path": [],
                "finish_reason": "error",
                "success": False,
                "error": str(e),
            }

    async def stream_command(
        self,
        command: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        capabilities: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream command execution with real-time updates.

        Args:
            command: User command
            conversation_history: Previous messages
            capabilities: Available capabilities
            context: Additional context

        Yields:
            Chunks of execution progress
        """
        # Build message history
        messages = conversation_history.copy() if conversation_history else []
        messages.append({"role": "user", "content": command})

        # Add capabilities to context
        context_vars = context or {}
        context_vars["capabilities"] = capabilities or []

        try:
            # For now, execute and yield result
            # Full streaming would require Swarm streaming support
            yield {"type": "status", "content": "Processing command..."}

            response = self.swarm.run(
                agent=self.coordinator,
                messages=messages,
                context_variables=context_vars,
                model_override=get_model_name(self.config),
                max_turns=15,
                debug=False,
            )

            # Yield content
            content = self._extract_content(response)
            if content:
                yield {"type": "content", "content": content}

            # Yield tool calls
            tool_calls = self._extract_tool_calls(response)
            for tool_call in tool_calls:
                yield {"type": "tool_call", "name": tool_call["name"], "arguments": tool_call["arguments"]}

            # Yield completion
            yield {"type": "finish", "reason": "stop"}

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    def _extract_content(self, response: Response) -> str:
        """Extract text content from Swarm response."""
        if not response.messages:
            return ""

        # Get last assistant message
        for msg in reversed(response.messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                return msg["content"]

        return ""

    def _extract_tool_calls(self, response: Response) -> List[Dict[str, Any]]:
        """Extract tool calls from Swarm response."""
        tool_calls = []

        for msg in response.messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    tool_calls.append({
                        "name": tc.get("function", {}).get("name", ""),
                        "arguments": tc.get("function", {}).get("arguments", "{}"),
                    })

        return tool_calls

    def _extract_agent_path(self, response: Response) -> List[str]:
        """Extract agent handoff path from response."""
        # Track which agents were involved
        agents = ["coordinator"]

        for msg in response.messages:
            if msg.get("role") == "assistant" and msg.get("sender"):
                agent_name = msg["sender"]
                if agent_name not in agents:
                    agents.append(agent_name)

        return agents

    def update_agent_capabilities(self, agent_name: str, capabilities: List[str]):
        """
        Update capabilities for a specific agent.

        Args:
            agent_name: Agent identifier
            capabilities: List of capability names
        """
        # This would update the agent's available tools
        # Implementation depends on how capabilities are managed
        pass


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
