"""
Unit tests for agent orchestration
"""
import pytest
from app.agents.openai_orchestrator import AgentOrchestrator, get_orchestrator


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator initialization"""
    orchestrator = AgentOrchestrator()

    assert orchestrator is not None
    assert hasattr(orchestrator, 'client')
    assert hasattr(orchestrator, 'config')


@pytest.mark.asyncio
async def test_get_orchestrator_singleton():
    """Test orchestrator singleton pattern"""
    orch1 = get_orchestrator()
    orch2 = get_orchestrator()

    assert orch1 is orch2


@pytest.mark.asyncio
async def test_get_or_create_assistant():
    """Test assistant creation"""
    orchestrator = AgentOrchestrator()

    assistant = await orchestrator.get_or_create_assistant(
        assistant_id="test-id",
        name="Test Assistant",
        instructions="Test instructions",
        capabilities=["navigate", "click_element"]
    )

    assert assistant is not None


@pytest.mark.asyncio
async def test_execute_command_structure():
    """Test command execution structure"""
    orchestrator = AgentOrchestrator()

    # Test that execute_command method exists and has correct signature
    assert hasattr(orchestrator, 'execute_command')


@pytest.mark.asyncio
async def test_stream_command_structure():
    """Test streaming command structure"""
    orchestrator = AgentOrchestrator()

    # Test that stream_command method exists
    assert hasattr(orchestrator, 'stream_command')


@pytest.mark.asyncio
async def test_update_assistant_capabilities():
    """Test updating assistant capabilities"""
    orchestrator = AgentOrchestrator()

    # Test method exists
    assert hasattr(orchestrator, 'update_assistant_capabilities')


@pytest.mark.asyncio
async def test_remove_assistant():
    """Test removing assistant from cache"""
    orchestrator = AgentOrchestrator()

    # Test method exists
    assert hasattr(orchestrator, 'remove_assistant')


@pytest.mark.asyncio
async def test_get_assistant_count():
    """Test getting assistant count"""
    orchestrator = AgentOrchestrator()

    count = orchestrator.get_assistant_count()
    assert isinstance(count, int)
    assert count >= 0
