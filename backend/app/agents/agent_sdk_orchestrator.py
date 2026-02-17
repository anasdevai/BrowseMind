"""
OpenAI Agent SDK implementation with multi-agent orchestration.
Uses Agent class, Runner, function_tool decorator, and handoffs.
"""
from typing import Any, Dict, List, Optional
from agents import Agent, Runner, function_tool, RunConfig, RunResult

from app.config.openrouter import get_llm_client, get_llm_config, get_model_name
from app.tools.base import get_tool_registry


# ============================================================================
# Tool Functions (decorated with @function_tool)
# ============================================================================

@function_tool
async def navigate_to_url(url: str, wait_until: str = "load") -> Dict[str, Any]:
    """
    Navigate to a URL in the browser.

    Args:
        url: The URL to navigate to
        wait_until: Wait condition (load, domcontentloaded, networkidle)

    Returns:
        Navigation result with success status
    """
    return {
        "action": "navigate",
        "params": {"url": url, "wait_until": wait_until},
        "requires_execution": True
    }


@function_tool
async def click_element(selector: Optional[str] = None, text: Optional[str] = None, index: int = 0) -> Dict[str, Any]:
    """
    Click an element on the page.

    Args:
        selector: CSS selector for the element
        text: Text content to find element by
        index: Index if multiple matches (default 0)

    Returns:
        Click action result
    """
    return {
        "action": "click_element",
        "params": {"selector": selector, "text": text, "index": index},
        "requires_execution": True
    }


@function_tool
async def type_text(selector: str, text: str, clear_first: bool = True, press_enter: bool = False) -> Dict[str, Any]:
    """
    Type text into an input field.

    Args:
        selector: CSS selector for the input
        text: Text to type
        clear_first: Clear existing text first
        press_enter: Press Enter after typing

    Returns:
        Type action result
    """
    return {
        "action": "type_text",
        "params": {"selector": selector, "text": text, "clear_first": clear_first, "press_enter": press_enter},
        "requires_execution": True
    }


@function_tool
async def scroll_page(direction: str, amount: int = 500, smooth: bool = True) -> Dict[str, Any]:
    """
    Scroll the page.

    Args:
        direction: Direction to scroll (up, down, top, bottom)
        amount: Amount to scroll in pixels
        smooth: Use smooth scrolling

    Returns:
        Scroll action result
    """
    return {
        "action": "scroll",
        "params": {"direction": direction, "amount": amount, "smooth": smooth},
        "requires_execution": True
    }


@function_tool
async def extract_text(selector: str, all: bool = False, trim: bool = True) -> Dict[str, Any]:
    """
    Extract text from elements.

    Args:
        selector: CSS selector for elements
        all: Extract from all matching elements
        trim: Trim whitespace

    Returns:
        Extraction action result
    """
    return {
        "action": "extract_text",
        "params": {"selector": selector, "all": all, "trim": trim},
        "requires_execution": True
    }


@function_tool
async def extract_links(selector: Optional[str] = None, filter_pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract links from the page.

    Args:
        selector: CSS selector for links (default: all links)
        filter_pattern: Regex pattern to filter URLs

    Returns:
        Links extraction result
    """
    return {
        "action": "extract_links",
        "params": {"selector": selector, "filter_pattern": filter_pattern},
        "requires_execution": True
    }


@function_tool
async def take_screenshot(selector: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
    """
    Take a screenshot.

    Args:
        selector: CSS selector for specific element
        full_page: Capture full page

    Returns:
        Screenshot action result
    """
    return {
        "action": "screenshot",
        "params": {"selector": selector, "full_page": full_page},
        "requires_execution": True
    }


# ============================================================================
# Specialized Agents with Handoffs
# ============================================================================

def create_navigation_agent() -> Agent:
    """Create navigation specialist agent."""
    return Agent(
        name="NavigationAgent",
        handoff_description="Specialist for navigating to URLs, scrolling pages, and taking screenshots",
        instructions="""You are a navigation specialist for web browsing.

Your expertise:
- Navigate to URLs with appropriate wait conditions
- Scroll pages to find content
- Take screenshots for documentation
- Handle page loading and navigation errors

When given a navigation task:
1. Use navigate_to_url with appropriate wait_until parameter
2. Verify navigation succeeded
3. Use scroll_page if content needs to be visible
4. Use take_screenshot to capture important states

Always confirm successful navigation before completing.""",
        tools=[navigate_to_url, scroll_page, take_screenshot]
    )


def create_extraction_agent() -> Agent:
    """Create data extraction specialist agent."""
    return Agent(
        name="ExtractionAgent",
        handoff_description="Specialist for extracting text, links, and data from web pages",
        instructions="""You are a data extraction specialist for web pages.

Your expertise:
- Extract text content from elements
- Extract links and URLs
- Get structured data from pages
- Handle multiple matching elements

When given an extraction task:
1. Identify the best CSS selector for target elements
2. Use extract_text for text content
3. Use extract_links for URLs
4. Format extracted data clearly
5. Handle cases where elements are not found

Always provide structured, clean data output.""",
        tools=[extract_text, extract_links]
    )


def create_interaction_agent() -> Agent:
    """Create interaction specialist agent."""
    return Agent(
        name="InteractionAgent",
        handoff_description="Specialist for clicking elements and typing text into forms",
        instructions="""You are an interaction specialist for web automation.

Your expertise:
- Click buttons, links, and elements
- Type text into input fields
- Fill out forms
- Handle interactive elements

When given an interaction task:
1. Identify target elements using CSS selectors or text
2. Use click_element for clicking
3. Use type_text for form inputs
4. Execute interactions in correct order
5. Report success or failure clearly

Always verify elements are accessible before interaction.""",
        tools=[click_element, type_text]
    )


def create_coordinator_agent(
    navigation_agent: Agent,
    extraction_agent: Agent,
    interaction_agent: Agent
) -> Agent:
    """Create main coordinator agent with handoffs."""
    return Agent(
        name="Coordinator",
        handoff_description="Main coordinator for browser automation tasks",
        instructions="""You are the main coordinator for BrowserMind browser automation.

Your role:
1. Understand user commands about web browsing
2. Break down complex tasks into subtasks
3. Hand off subtasks to appropriate specialist agents
4. Coordinate multi-step workflows
5. Synthesize results from specialists

Task routing:
- Navigation tasks (go to URL, scroll) → Hand off to NavigationAgent
- Extraction tasks (get text, extract links) → Hand off to ExtractionAgent
- Interaction tasks (click, type, fill form) → Hand off to InteractionAgent

For complex tasks:
1. Break into sequential steps
2. Hand off each step to appropriate specialist
3. Pass context between specialists
4. Synthesize final result

Always provide clear, actionable responses.""",
        tools=[],  # Coordinator doesn't use tools directly, only handoffs
        handoffs=[navigation_agent, extraction_agent, interaction_agent]
    )


# ============================================================================
# Agent Orchestrator using OpenAI Agent SDK
# ============================================================================

class AgentSDKOrchestrator:
    """
    Orchestrator using OpenAI Agent SDK with multi-agent handoffs.
    """

    def __init__(self):
        """Initialize orchestrator with specialized agents."""
        from agents import OpenAIProvider

        self.config = get_llm_config()
        self.model = get_model_name(self.config)

        # Configure Agent SDK to use OpenRouter as provider
        if self.config.llm_provider == "openrouter":
            self.model_provider = OpenAIProvider(
                api_key=self.config.openrouter_api_key,
                base_url=self.config.openrouter_base_url
            )
        else:
            self.model_provider = OpenAIProvider(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url
            )

        # Create specialized agents
        self.navigation_agent = create_navigation_agent()
        self.extraction_agent = create_extraction_agent()
        self.interaction_agent = create_interaction_agent()

        # Create coordinator with handoffs
        self.coordinator = create_coordinator_agent(
            self.navigation_agent,
            self.extraction_agent,
            self.interaction_agent
        )

    async def execute_command(
        self,
        command: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        capabilities: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        Execute a command using Agent SDK with handoffs.

        Args:
            command: User command
            conversation_history: Previous messages
            capabilities: Available capabilities
            context: Additional context
            max_turns: Maximum agent turns

        Returns:
            Execution result
        """
        try:
            # Create model settings
            from agents import ModelSettings
            model_settings = ModelSettings(
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Create run config
            run_config = RunConfig(
                model=self.model,
                model_provider=self.model_provider,
                model_settings=model_settings
            )

            # Run coordinator agent
            result: RunResult = await Runner.run(
                starting_agent=self.coordinator,
                input=command,
                max_turns=max_turns,
                run_config=run_config
            )

            # Extract tool calls and content
            tool_calls = []
            for message in result.messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tc in message.tool_calls:
                        tool_calls.append({
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        })

            return {
                "content": result.final_output or "",
                "tool_calls": tool_calls,
                "agent_path": self._extract_agent_path(result),
                "finish_reason": "stop",
                "success": True
            }

        except Exception as e:
            return {
                "content": f"Error executing command: {str(e)}",
                "tool_calls": [],
                "agent_path": [],
                "finish_reason": "error",
                "success": False,
                "error": str(e)
            }

    async def stream_command(
        self,
        command: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        capabilities: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        max_turns: int = 10
    ):
        """
        Stream command execution with real-time updates.

        Args:
            command: User command
            conversation_history: Previous messages
            capabilities: Available capabilities
            context: Additional context
            max_turns: Maximum agent turns

        Yields:
            Execution progress chunks
        """
        try:
            yield {"type": "status", "content": "Processing command..."}

            # Create model settings
            from agents import ModelSettings
            model_settings = ModelSettings(
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )

            # Create run config
            run_config = RunConfig(
                model=self.model,
                model_provider=self.model_provider,
                model_settings=model_settings
            )

            # Run coordinator agent
            result: RunResult = await Runner.run(
                starting_agent=self.coordinator,
                input=command,
                max_turns=max_turns,
                run_config=run_config
            )

            # Yield content
            if result.final_output:
                yield {"type": "content", "content": result.final_output}

            # Yield tool calls
            for message in result.messages:
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tc in message.tool_calls:
                        yield {
                            "type": "tool_call",
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }

            # Yield completion
            yield {"type": "finish", "reason": "stop"}

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    def _extract_agent_path(self, result: RunResult) -> List[str]:
        """Extract agent handoff path from result."""
        agents = ["Coordinator"]

        for message in result.messages:
            if hasattr(message, 'sender') and message.sender:
                agent_name = message.sender
                if agent_name not in agents:
                    agents.append(agent_name)

        return agents


# Global orchestrator instance
_orchestrator: Optional[AgentSDKOrchestrator] = None


def get_agent_sdk_orchestrator() -> AgentSDKOrchestrator:
    """
    Get or create the global Agent SDK orchestrator instance.

    Returns:
        AgentSDKOrchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = AgentSDKOrchestrator()

    return _orchestrator
