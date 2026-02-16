"""
Command queue with timeout management.
Handles command queueing, execution tracking, and 30-second timeout enforcement.
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class CommandStatus(Enum):
    """Command execution status."""
    QUEUED = "queued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class Command:
    """
    Queued command waiting for execution.
    In-memory entity (not persisted to database).
    """
    id: str
    assistant_id: str
    session_id: str
    text: str
    status: CommandStatus = CommandStatus.QUEUED
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(seconds=30))
    result: Any = None
    error: Optional[str] = None
    connection_id: Optional[str] = None  # WebSocket connection that issued command

    def is_expired(self) -> bool:
        """Check if command has exceeded timeout."""
        return datetime.utcnow() > self.timeout_at

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds since command was queued."""
        return (datetime.utcnow() - self.queued_at).total_seconds()


class CommandQueue:
    """
    Manages command queue with timeout enforcement.
    Supports concurrent execution with configurable limits.
    """

    def __init__(self, max_queued_per_assistant: int = 10, max_concurrent: int = 5):
        """
        Initialize command queue.

        Args:
            max_queued_per_assistant: Maximum queued commands per assistant
            max_concurrent: Maximum concurrent executing commands
        """
        self.max_queued_per_assistant = max_queued_per_assistant
        self.max_concurrent = max_concurrent

        # All commands: command_id -> Command
        self._commands: Dict[str, Command] = {}

        # Queued commands by assistant: assistant_id -> List[command_id]
        self._queued_by_assistant: Dict[str, List[str]] = {}

        # Currently executing commands: Set[command_id]
        self._executing: set = set()

        # Timeout monitor task
        self._timeout_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def enqueue(
        self,
        assistant_id: str,
        session_id: str,
        text: str,
        connection_id: Optional[str] = None
    ) -> Command:
        """
        Add a command to the queue.

        Args:
            assistant_id: Target assistant UUID
            session_id: Associated session UUID
            text: Command text
            connection_id: WebSocket connection ID

        Returns:
            Created Command object

        Raises:
            ValueError: If queue is full for this assistant
        """
        # Check queue limit for this assistant
        queued_count = len(self._queued_by_assistant.get(assistant_id, []))
        if queued_count >= self.max_queued_per_assistant:
            raise ValueError(f"Queue full for assistant {assistant_id} (max {self.max_queued_per_assistant})")

        # Create command
        command = Command(
            id=str(uuid4()),
            assistant_id=assistant_id,
            session_id=session_id,
            text=text,
            connection_id=connection_id
        )

        # Store command
        self._commands[command.id] = command

        # Add to assistant queue
        if assistant_id not in self._queued_by_assistant:
            self._queued_by_assistant[assistant_id] = []
        self._queued_by_assistant[assistant_id].append(command.id)

        print(f"Command queued: {command.id} for assistant {assistant_id}")
        return command

    async def start_execution(self, command_id: str) -> None:
        """
        Mark a command as executing.

        Args:
            command_id: Command ID to start

        Raises:
            KeyError: If command not found
            ValueError: If max concurrent limit reached
        """
        if command_id not in self._commands:
            raise KeyError(f"Command {command_id} not found")

        if len(self._executing) >= self.max_concurrent:
            raise ValueError(f"Max concurrent executions reached ({self.max_concurrent})")

        command = self._commands[command_id]
        command.status = CommandStatus.EXECUTING
        command.started_at = datetime.utcnow()

        # Move from queued to executing
        self._executing.add(command_id)
        if command.assistant_id in self._queued_by_assistant:
            if command_id in self._queued_by_assistant[command.assistant_id]:
                self._queued_by_assistant[command.assistant_id].remove(command_id)

        print(f"Command executing: {command_id}")

    async def complete(self, command_id: str, result: Any = None) -> None:
        """
        Mark a command as completed.

        Args:
            command_id: Command ID
            result: Execution result
        """
        if command_id not in self._commands:
            return

        command = self._commands[command_id]
        command.status = CommandStatus.COMPLETED
        command.completed_at = datetime.utcnow()
        command.result = result

        # Remove from executing
        self._executing.discard(command_id)

        print(f"Command completed: {command_id}")

    async def fail(self, command_id: str, error: str) -> None:
        """
        Mark a command as failed.

        Args:
            command_id: Command ID
            error: Error message
        """
        if command_id not in self._commands:
            return

        command = self._commands[command_id]
        command.status = CommandStatus.FAILED
        command.completed_at = datetime.utcnow()
        command.error = error

        # Remove from executing
        self._executing.discard(command_id)

        print(f"Command failed: {command_id} - {error}")

    async def cancel(self, command_id: str) -> bool:
        """
        Cancel a queued or executing command.

        Args:
            command_id: Command ID to cancel

        Returns:
            True if cancelled, False if not found or already completed
        """
        if command_id not in self._commands:
            return False

        command = self._commands[command_id]

        # Can only cancel queued or executing commands
        if command.status not in [CommandStatus.QUEUED, CommandStatus.EXECUTING]:
            return False

        command.status = CommandStatus.CANCELLED
        command.completed_at = datetime.utcnow()

        # Remove from queued or executing
        if command.assistant_id in self._queued_by_assistant:
            if command_id in self._queued_by_assistant[command.assistant_id]:
                self._queued_by_assistant[command.assistant_id].remove(command_id)
        self._executing.discard(command_id)

        print(f"Command cancelled: {command_id}")
        return True

    async def timeout(self, command_id: str) -> None:
        """
        Mark a command as timed out.

        Args:
            command_id: Command ID
        """
        if command_id not in self._commands:
            return

        command = self._commands[command_id]
        command.status = CommandStatus.TIMEOUT
        command.completed_at = datetime.utcnow()
        command.error = "Command execution exceeded 30 second timeout"

        # Remove from executing
        self._executing.discard(command_id)

        print(f"Command timed out: {command_id}")

    def get_command(self, command_id: str) -> Optional[Command]:
        """Get command by ID."""
        return self._commands.get(command_id)

    def get_queued_commands(self, assistant_id: str) -> List[Command]:
        """Get all queued commands for an assistant."""
        command_ids = self._queued_by_assistant.get(assistant_id, [])
        return [self._commands[cid] for cid in command_ids if cid in self._commands]

    def get_executing_commands(self) -> List[Command]:
        """Get all currently executing commands."""
        return [self._commands[cid] for cid in self._executing if cid in self._commands]

    def get_queue_status(self) -> dict:
        """
        Get overall queue status.

        Returns:
            Dictionary with queue statistics
        """
        return {
            "total_commands": len(self._commands),
            "queued": sum(len(cmds) for cmds in self._queued_by_assistant.values()),
            "executing": len(self._executing),
            "max_concurrent": self.max_concurrent,
            "assistants_with_queued": len(self._queued_by_assistant)
        }

    async def start_timeout_monitor(self) -> None:
        """Start the timeout monitoring task."""
        if self._is_running:
            return

        self._is_running = True
        self._timeout_task = asyncio.create_task(self._timeout_monitor_loop())
        print("Command timeout monitor started")

    async def stop_timeout_monitor(self) -> None:
        """Stop the timeout monitoring task."""
        self._is_running = False
        if self._timeout_task:
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
        print("Command timeout monitor stopped")

    async def _timeout_monitor_loop(self) -> None:
        """Monitor for timed out commands."""
        while self._is_running:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                await self._check_timeouts()
                await self._cleanup_old_commands()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in timeout monitor: {e}")

    async def _check_timeouts(self) -> None:
        """Check for and timeout expired commands."""
        now = datetime.utcnow()

        # Check executing commands for timeout
        for command_id in list(self._executing):
            command = self._commands.get(command_id)
            if command and command.is_expired():
                await self.timeout(command_id)

        # Check queued commands for timeout
        for assistant_id, command_ids in list(self._queued_by_assistant.items()):
            for command_id in list(command_ids):
                command = self._commands.get(command_id)
                if command and command.is_expired():
                    await self.timeout(command_id)

    async def _cleanup_old_commands(self) -> None:
        """Remove commands older than 5 minutes from memory."""
        cutoff = datetime.utcnow() - timedelta(minutes=5)

        for command_id in list(self._commands.keys()):
            command = self._commands[command_id]
            if command.queued_at < cutoff and command.status in [
                CommandStatus.COMPLETED,
                CommandStatus.FAILED,
                CommandStatus.CANCELLED,
                CommandStatus.TIMEOUT
            ]:
                del self._commands[command_id]


# Global command queue instance
_command_queue: CommandQueue = None


def get_command_queue() -> CommandQueue:
    """
    Get or create the global command queue instance.

    Returns:
        CommandQueue instance
    """
    global _command_queue
    if _command_queue is None:
        _command_queue = CommandQueue()
    return _command_queue
