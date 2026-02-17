"""
Swarm-based agent system for BrowserMind.
Uses OpenAI Agent SDK (Swarm) for multi-agent orchestration.
"""
from typing import Any, Callable, Dict, List, Optional

from swarm import Agent, Swarm
from swarm.types import Response

from app.config.openrouter import get_llm_client, get_llm_config, get_model_name
from app.tools.base import get_tool_registry


class BrowserAgent:
    """
    Browser control agent using Swarm framework.
    Handles natural language commands for browser automation.
    """

    def __init__(self, name: str = "BrowserAgent", capabilities: Optional[List[str]] = None):
        """
        Initialize browser agent.

        Args:
            name: Agent name
            capabilities: List of capability names this agent can use
        """
        self.name = name
        self.capabilities = capabilities or []
        self.swarm = Swarm(client=get_llm_client())
        self.config = get_llm_config()

        # Build tool functions for Swarm
        self.functions = self._build_tool_functions()

        # Create Swarm agent
        self.agent = Agent(
            name=self.name,
            model=get_model_name(self.config),
            instructions=self._get_instructions(),
            functions=self.functions,
        )

    def _get_instructions(self) -> str:
        """
        Get agent instructions based on capabilities.

        Returns:
            System instructions string
        """
        base_instructions = """You are BrowserMind, an AI assistant that controls web browsers through natural language.

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
- Report errors clearly and suggest fixes"""

        if self.capabilities:
            capabilities_str = ", ".join(self.capabilities)
            base_instructions += f"\n\nAvailable capabilities: {capabilities_str}"
            base_instructions += "\n\nYou can ONLY use tools that match your granted capabilities."

        return base_instructions

    def _build_tool_functions(self) -> List[Callable]:
        """
        Build Swarm-compatible tool functions from registry.

        Returns:
            List of callable functions for Swarm
        """
        registry = get_tool_registry()
        functions = []

        for tool_name in self.capabilities:
            tool = registry.get_tool(tool_name)
            if tool:
                # Create Swarm-compatible function
                func = self._create_swarm_function(tool)
                functions.append(func)

        return functions

    def _create_swarm_function(self, tool) -> Callable:
        """
        Create a Swarm-compatible function from a Tool instance.

        Args:
            tool: Tool instance

        Returns:
            Callable function with proper signature and docstring
        """

        async def tool_function(**kwargs) -> Dict[str, Any]:
            """Execute tool and return result."""
            try:
                result = await tool.execute(kwargs)
                return result
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Set function metadata for Swarm
        tool_function.__name__ = tool.name
        tool_function.__doc__ = f"{tool.description}\n\nParameters: {tool.get_schema()}"

        return tool_function

    async def run(
        self, message: str, context_variables: Optional[Dict[str, Any]] = None
    ) -> Response:
        """
        Run agent with a message.

        Args:
            message: User message
            context_variables: Context variables for the agent

        Returns:
            Swarm Response object
        """
        messages = [{"role": "user", "content": message}]

        response = self.swarm.run(
            agent=self.agent,
            messages=messages,
            context_variables=context_variables or {},
            model_override=get_model_name(self.config),
            max_turns=10,
        )

        return response

    async def run_with_history(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        context_variables: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """
        Run agent with conversation history.

        Args:
            message: User message
            conversation_history: Previous messages
            context_variables: Context variables

        Returns:
            Swarm Response object
        """
        # Build message list
        messages = conversation_history.copy()
        messages.append({"role": "user", "content": message})

        response = self.swarm.run(
            agent=self.agent,
            messages=messages,
            context_variables=context_variables or {},
            model_override=get_model_name(self.config),
            max_turns=10,
        )

        return response


class SpecialistAgent:
    """
    Specialist agent for specific tasks (extraction, navigation, etc.).
    """

    def __init__(
        self,
        name: str,
        specialty: str,
        capabilities: List[str],
        instructions: str,
    ):
        """
        Initialize specialist agent.

        Args:
            name: Agent name
            specialty: Agent specialty (extraction, navigation, etc.)
            capabilities: List of capability names
            instructions: Custom instructions
        """
        self.name = name
        self.specialty = specialty
        self.capabilities = capabilities
        self.swarm = Swarm(client=get_llm_client())
        self.config = get_llm_config()

        # Build tool functions
        self.functions = self._build_tool_functions()

        # Create Swarm agent
        self.agent = Agent(
            name=self.name,
            model=get_model_name(self.config),
            instructions=instructions,
            functions=self.functions,
        )

    def _build_tool_functions(self) -> List[Callable]:
        """Build tool functions for this specialist."""
        registry = get_tool_registry()
        functions = []

        for tool_name in self.capabilities:
            tool = registry.get_tool(tool_name)
            if tool:
                func = self._create_swarm_function(tool)
                functions.append(func)

        return functions

    def _create_swarm_function(self, tool) -> Callable:
        """Create Swarm-compatible function."""

        async def tool_function(**kwargs) -> Dict[str, Any]:
            try:
                result = await tool.execute(kwargs)
                return result
            except Exception as e:
                return {"success": False, "error": str(e)}

        tool_function.__name__ = tool.name
        tool_function.__doc__ = f"{tool.description}\n\nParameters: {tool.get_schema()}"

        return tool_function

    async def run(
        self, message: str, context_variables: Optional[Dict[str, Any]] = None
    ) -> Response:
        """Run specialist agent."""
        messages = [{"role": "user", "content": message}]

        response = self.swarm.run(
            agent=self.agent,
            messages=messages,
            context_variables=context_variables or {},
            model_override=get_model_name(self.config),
            max_turns=5,
        )

        return response
