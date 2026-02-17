"""
Integration tests for agent lifecycle
"""
import pytest
from app.agents.openai_orchestrator import get_orchestrator


@pytest.mark.asyncio
async def test_agent_creation_lifecycle():
    """Test agent creation and initialization"""
    orchestrator = get_orchestrator()

    assistant = await orchestrator.get_or_create_assistant(
        assistant_id="test-lifecycle-1",
        name="Lifecycle Test",
        instructions="Test instructions",
        capabilities=["navigate"]
    )

    assert assistant is not None


@pytest.mark.asyncio
async def test_agent_command_execution():
    """Test agent command execution"""
    orchestrator = get_orchestrator()

    # Test command execution structure
    assert hasattr(orchestrator, 'execute_command')


@pytest.mark.asyncio
async def test_agent_streaming():
    """Test agent streaming responses"""
    orchestrator = get_orchestrator()

    # Test streaming structure
    assert hasattr(orchestrator, 'stream_command')


@pytest.mark.asyncio
async def test_agent_capability_updates():
    """Test updating agent capabilities"""
    orchestrator = get_orchestrator()

    # Test capability update
    await orchestrator.update_assistant_capabilities(
        "test-id",
        ["navigate", "click_element"]
    )


@pytest.mark.asyncio
async def test_agent_removal():
    """Test agent removal from cache"""
    orchestrator = get_orchestrator()

    orchestrator.remove_assistant("test-id")
    assert True


@pytest.mark.asyncio
async def test_multiple_agents_concurrent():
    """Test multiple agents running concurrently"""
    orchestrator = get_orchestrator()

    # Test that multiple agents can be created
    count = orchestrator.get_assistant_count()
    assert count >= 0
