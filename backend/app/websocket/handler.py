"""
WebSocket message handler.
Routes incoming messages to appropriate handlers based on message type.
"""
import json
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.agents.main_agent import MainAgent
from app.db.models import Assistant, Message, Session as DBSession
from app.db.session import get_db_session
from app.tools.permission_validator import PermissionValidator
from app.websocket.manager import ConnectionManager
from app.websocket.queue import Command, CommandQueue, CommandStatus


class MessageHandler:
    """
    Routes WebSocket messages to appropriate handlers.
    Supports 17 message types from the protocol specification.
    """

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.agent = MainAgent()
        self.command_queue = CommandQueue()

        # Message type handlers: type -> handler function
        self._handlers: Dict[str, Callable] = {}

        # Register default handlers
        self._register_default_handlers()

    async def _handle_list_sessions(self, connection_id: str, message: dict) -> None:
        """Handle session list request with pagination."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        assistant_id = payload.get("assistant_id")
        limit = min(payload.get("limit", 50), 100)  # Max 100 per request
        offset = payload.get("offset", 0)
        include_archived = payload.get("include_archived", False)

        with get_db_session() as db:
            from app.db.session_manager import SessionManager
            session_manager = SessionManager(db)

            # Get sessions
            sessions = session_manager.list_sessions(
                assistant_id=assistant_id,
                limit=limit,
                offset=offset,
                include_archived=include_archived
            )

            # Build session list with metadata
            session_list = []
            for session in sessions:
                summary = session_manager.get_session_summary(session.id)
                if summary:
                    session_list.append(summary)

            # Send session list
            await self.connection_manager.send_message(connection_id, {
                "type": "session_list",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "sessions": session_list,
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(session_list) == limit
                }
            })

    async def _stream_command_response(
        self,
        connection_id: str,
        command_text: str,
        conversation_history: list,
        capabilities: list,
        session_id: str,
        correlation_id: str
    ) -> None:
        """
        Stream command response with real-time updates.

        Args:
            connection_id: WebSocket connection ID
            command_text: User command
            conversation_history: Previous messages
            capabilities: Available capabilities
            session_id: Database session ID
            correlation_id: Original message ID
        """
        accumulated_content = ""

        try:
            async for chunk in self.agent.stream_command(
                command=command_text,
                conversation_history=conversation_history,
                available_capabilities=capabilities
            ):
                chunk_type = chunk.get("type")

                if chunk_type == "content":
                    # Stream text content
                    content = chunk.get("content", "")
                    accumulated_content += content

                    await self.connection_manager.send_message(connection_id, {
                        "type": "response_chunk",
                        "id": str(uuid4()),
                        "timestamp": int(datetime.utcnow().timestamp() * 1000),
                        "correlation_id": correlation_id,
                        "payload": {
                            "content": content,
                            "done": False
                        }
                    })

                elif chunk_type == "tool_call":
                    # Handle tool call in stream
                    tool_name = chunk.get("name")
                    tool_args_str = chunk.get("arguments", "{}")

                    if tool_name:
                        try:
                            tool_args = json.loads(tool_args_str)

                            # Validate permission
                            with get_db_session() as db:
                                validator = PermissionValidator(db)
                                allowed, error_msg = validator.validate_tool_permission(
                                    session_id,  # Using session_id as placeholder
                                    tool_name
                                )

                            if allowed:
                                await self.send_tool_execution(
                                    connection_id,
                                    tool_name,
                                    tool_args,
                                    correlation_id
                                )
                            else:
                                await self._send_error(
                                    connection_id,
                                    error_msg,
                                    "PERMISSION_DENIED",
                                    correlation_id=correlation_id
                                )
                        except json.JSONDecodeError:
                            pass  # Incomplete tool arguments, wait for more chunks

                elif chunk_type == "finish":
                    # Send final chunk
                    await self.connection_manager.send_message(connection_id, {
                        "type": "response_chunk",
                        "id": str(uuid4()),
                        "timestamp": int(datetime.utcnow().timestamp() * 1000),
                        "correlation_id": correlation_id,
                        "payload": {
                            "content": "",
                            "done": True,
                            "finish_reason": chunk.get("reason", "stop")
                        }
                    })

                elif chunk_type == "error":
                    await self._send_error(
                        connection_id,
                        chunk.get("error", "Unknown error"),
                        "STREAMING_ERROR",
                        correlation_id=correlation_id
                    )
                    return

            # Save accumulated response to database
            if accumulated_content:
                with get_db_session() as db:
                    assistant_message = Message(
                        session_id=session_id,
                        role="assistant",
                        content=accumulated_content
                    )
                    db.add(assistant_message)
                    db.commit()

        except Exception as e:
            print(f"Error streaming response: {e}")
            await self._send_error(
                connection_id,
                f"Streaming error: {str(e)}",
                "STREAMING_ERROR",
                correlation_id=correlation_id
            )

    def _register_default_handlers(self) -> None:
        """Register built-in message handlers."""
        # Client → Server handlers
        self.register_handler("command", self._handle_command)
        self.register_handler("command_stream", self._handle_command_stream)
        self.register_handler("tool_result", self._handle_tool_result)
        self.register_handler("cancel_command", self._handle_cancel_command)
        self.register_handler("list_assistants", self._handle_list_assistants)
        self.register_handler("create_assistant", self._handle_create_assistant)
        self.register_handler("activate_assistant", self._handle_activate_assistant)
        self.register_handler("deactivate_assistant", self._handle_deactivate_assistant)
        self.register_handler("delete_assistant", self._handle_delete_assistant)
        self.register_handler("list_sessions", self._handle_list_sessions)
        self.register_handler("get_queue_status", self._handle_get_queue_status)
        self.register_handler("archive_session", self._handle_archive_session)
        self.register_handler("ping", self._handle_ping)

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a handler function for a message type.

        Args:
            message_type: Message type identifier
            handler: Async function to handle the message
        """
        self._handlers[message_type] = handler

    async def handle_message(
        self,
        connection_id: str,
        message: dict
    ) -> None:
        """
        Route an incoming message to the appropriate handler.

        Args:
            connection_id: Connection ID that sent the message
            message: Parsed JSON message

        Raises:
            ValueError: If message format is invalid
        """
        # Validate message structure
        if not isinstance(message, dict):
            await self._send_error(connection_id, "Invalid message format", "INVALID_FORMAT")
            return

        message_type = message.get("type")
        if not message_type:
            await self._send_error(connection_id, "Missing message type", "MISSING_TYPE")
            return

        message_id = message.get("id")
        if not message_id:
            await self._send_error(connection_id, "Missing message ID", "MISSING_ID")
            return

        # Get handler for message type
        handler = self._handlers.get(message_type)
        if not handler:
            await self._send_error(
                connection_id,
                f"Unknown message type: {message_type}",
                "UNKNOWN_TYPE",
                correlation_id=message_id
            )
            return

        # Execute handler
        try:
            await handler(connection_id, message)
        except Exception as e:
            print(f"Error handling message {message_type}: {e}")
            await self._send_error(
                connection_id,
                f"Internal error: {str(e)}",
                "INTERNAL_ERROR",
                correlation_id=message_id
            )

    # ========== Client → Server Handlers ==========

    async def _handle_command_stream(self, connection_id: str, message: dict) -> None:
        """Handle streaming command execution request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        command_text = payload.get("command")
        assistant_id = payload.get("assistant_id")
        session_id = payload.get("session_id")

        # Validate required fields
        if not command_text:
            await self._send_error(
                connection_id,
                "Missing command text",
                "MISSING_COMMAND",
                correlation_id=message["id"]
            )
            return

        if not assistant_id:
            await self._send_error(
                connection_id,
                "Missing assistant_id",
                "MISSING_ASSISTANT",
                correlation_id=message["id"]
            )
            return

        if not session_id:
            await self._send_error(
                connection_id,
                "Missing session_id",
                "MISSING_SESSION",
                correlation_id=message["id"]
            )
            return

        # Get database session
        with get_db_session() as db:
            # Verify assistant exists and is active
            assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
            if not assistant:
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} not found",
                    "ASSISTANT_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            if assistant.status != "active":
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} is not active",
                    "ASSISTANT_INACTIVE",
                    correlation_id=message["id"]
                )
                return

            # Get assistant capabilities
            validator = PermissionValidator(db)
            capabilities = validator.get_assistant_capabilities(assistant_id)

            # Get conversation history
            db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not db_session:
                await self._send_error(
                    connection_id,
                    f"Session {session_id} not found",
                    "SESSION_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            # Get recent messages for context
            messages = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(20)
                .all()
            )
            messages.reverse()  # Oldest first

            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # Save user message
            user_message = Message(
                session_id=session_id,
                role="user",
                content=command_text
            )
            db.add(user_message)
            db.commit()

        # Send status update
        await self.send_status_update(
            connection_id,
            "executing",
            "Processing command...",
            message["id"]
        )

        # Stream response
        await self._stream_command_response(
            connection_id,
            command_text,
            conversation_history,
            capabilities,
            session_id,
            message["id"]
        )

        # Send completion status
        await self.send_status_update(
            connection_id,
            "completed",
            "Command completed",
            message["id"]
        )

    async def _handle_command(self, connection_id: str, message: dict) -> None:
        """Handle command execution request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        command_text = payload.get("command")
        assistant_id = payload.get("assistant_id")
        session_id = payload.get("session_id")

        # Validate required fields
        if not command_text:
            await self._send_error(
                connection_id,
                "Missing command text",
                "MISSING_COMMAND",
                correlation_id=message["id"]
            )
            return

        if not assistant_id:
            await self._send_error(
                connection_id,
                "Missing assistant_id",
                "MISSING_ASSISTANT",
                correlation_id=message["id"]
            )
            return

        if not session_id:
            await self._send_error(
                connection_id,
                "Missing session_id",
                "MISSING_SESSION",
                correlation_id=message["id"]
            )
            return

        # Get database session
        with get_db_session() as db:
            # Verify assistant exists and is active
            assistant = db.query(Assistant).filter(Assistant.id == assistant_id).first()
            if not assistant:
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} not found",
                    "ASSISTANT_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            if assistant.status != "active":
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} is not active",
                    "ASSISTANT_INACTIVE",
                    correlation_id=message["id"]
                )
                return

            # Get assistant capabilities
            validator = PermissionValidator(db)
            capabilities = validator.get_assistant_capabilities(assistant_id)

            # Get conversation history
            db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
            if not db_session:
                await self._send_error(
                    connection_id,
                    f"Session {session_id} not found",
                    "SESSION_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            # Get recent messages for context
            messages = (
                db.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(20)
                .all()
            )
            messages.reverse()  # Oldest first

            conversation_history = []
            for msg in messages:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # Save user message
            user_message = Message(
                session_id=session_id,
                role="user",
                content=command_text
            )
            db.add(user_message)
            db.commit()

        # Send status update
        await self.send_status_update(
            connection_id,
            "executing",
            "Processing command...",
            message["id"]
        )

        # Process command with agent
        try:
            response = await self.agent.process_command(
                command=command_text,
                conversation_history=conversation_history,
                available_capabilities=capabilities
            )

            # Save assistant response
            with get_db_session() as db:
                assistant_message = Message(
                    session_id=session_id,
                    role="assistant",
                    content=response["content"]
                )
                db.add(assistant_message)
                db.commit()

            # Send response to client
            await self.connection_manager.send_message(connection_id, {
                "type": "response",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "content": response["content"],
                    "finish_reason": response["finish_reason"]
                }
            })

            # Handle tool calls
            if response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    tool_name = tool_call["name"]
                    tool_args = json.loads(tool_call["arguments"])

                    # Validate permission
                    with get_db_session() as db:
                        validator = PermissionValidator(db)
                        allowed, error_msg = validator.validate_tool_permission(
                            assistant_id,
                            tool_name
                        )

                    if not allowed:
                        await self._send_error(
                            connection_id,
                            error_msg,
                            "PERMISSION_DENIED",
                            correlation_id=message["id"]
                        )
                        continue

                    # Send tool execution request to extension
                    await self.send_tool_execution(
                        connection_id,
                        tool_name,
                        tool_args,
                        message["id"]
                    )

            # Send completion status
            await self.send_status_update(
                connection_id,
                "completed",
                "Command completed",
                message["id"]
            )

        except Exception as e:
            print(f"Error processing command: {e}")
            await self._send_error(
                connection_id,
                f"Error processing command: {str(e)}",
                "PROCESSING_ERROR",
                correlation_id=message["id"]
            )
            await self.send_status_update(
                connection_id,
                "failed",
                f"Command failed: {str(e)}",
                message["id"]
            )

    async def _handle_tool_result(self, connection_id: str, message: dict) -> None:
        """Handle tool execution result from extension."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        tool_name = payload.get("tool")
        result = payload.get("result")
        success = payload.get("success", True)
        correlation_id = message.get("correlation_id")

        if not tool_name:
            await self._send_error(
                connection_id,
                "Missing tool name in result",
                "MISSING_TOOL",
                correlation_id=correlation_id
            )
            return

        # Get session and assistant from correlation
        # For now, just send the result back to the client
        # In a full implementation, we would:
        # 1. Look up the original command from correlation_id
        # 2. Pass the result back to the agent for interpretation
        # 3. Continue the conversation if needed

        if success:
            await self.connection_manager.send_message(connection_id, {
                "type": "response",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": correlation_id,
                "payload": {
                    "content": f"Tool {tool_name} executed successfully. Result: {json.dumps(result)}",
                    "finish_reason": "stop"
                }
            })
        else:
            error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
            await self._send_error(
                connection_id,
                f"Tool {tool_name} failed: {error_msg}",
                "TOOL_EXECUTION_FAILED",
                correlation_id=correlation_id
            )

    async def _handle_cancel_command(self, connection_id: str, message: dict) -> None:
        """Handle command cancellation request."""
        # TODO: Implement in Phase 6 (User Story 4)
        # Will cancel queued command
        await self._send_ack(connection_id, message["id"])

    async def _handle_list_assistants(self, connection_id: str, message: dict) -> None:
        """Handle request for assistant list."""
        await self._send_ack(connection_id, message["id"])

        with get_db_session() as db:
            # Get all assistants (including inactive)
            assistants = db.query(Assistant).filter(
                Assistant.deleted_at.is_(None)
            ).all()

            assistant_list = []
            for assistant in assistants:
                # Get capability count
                capability_count = db.query(AssistantCapability).filter(
                    AssistantCapability.assistant_id == assistant.id
                ).count()

                assistant_list.append({
                    "id": assistant.id,
                    "name": assistant.name,
                    "instructions": assistant.instructions,
                    "status": assistant.status,
                    "capability_count": capability_count,
                    "created_at": assistant.created_at.isoformat(),
                    "updated_at": assistant.updated_at.isoformat(),
                })

            # Send assistant list
            await self.connection_manager.send_message(connection_id, {
                "type": "assistant_list",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "assistants": assistant_list
                }
            })

    async def _handle_create_assistant(self, connection_id: str, message: dict) -> None:
        """Handle assistant creation request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        name = payload.get("name")
        instructions = payload.get("instructions", "")
        capability_names = payload.get("capabilities", [])

        # Validate required fields
        if not name:
            await self._send_error(
                connection_id,
                "Missing assistant name",
                "MISSING_NAME",
                correlation_id=message["id"]
            )
            return

        with get_db_session() as db:
            # Check assistant count limit (max 20)
            assistant_count = db.query(Assistant).filter(
                Assistant.deleted_at.is_(None)
            ).count()

            if assistant_count >= 20:
                await self._send_error(
                    connection_id,
                    "Maximum 20 assistants allowed",
                    "MAX_ASSISTANTS_EXCEEDED",
                    correlation_id=message["id"]
                )
                return

            # Validate capabilities
            if len(capability_names) > 10:
                await self._send_error(
                    connection_id,
                    "Maximum 10 capabilities per assistant",
                    "MAX_CAPABILITIES_EXCEEDED",
                    correlation_id=message["id"]
                )
                return

            # Verify all capabilities exist
            capabilities = db.query(Capability).filter(
                Capability.name.in_(capability_names),
                Capability.enabled == True
            ).all()

            if len(capabilities) != len(capability_names):
                found_names = {cap.name for cap in capabilities}
                missing = set(capability_names) - found_names
                await self._send_error(
                    connection_id,
                    f"Invalid capabilities: {', '.join(missing)}",
                    "INVALID_CAPABILITIES",
                    correlation_id=message["id"]
                )
                return

            # Create assistant
            assistant = Assistant(
                name=name,
                instructions=instructions,
                status="inactive"  # New assistants start inactive
            )
            db.add(assistant)
            db.flush()  # Get assistant ID

            # Add capabilities
            for capability in capabilities:
                assoc = AssistantCapability(
                    assistant_id=assistant.id,
                    capability_id=capability.id
                )
                db.add(assoc)

            db.commit()
            db.refresh(assistant)

            # Send success response
            await self.connection_manager.send_message(connection_id, {
                "type": "assistant_created",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "assistant": {
                        "id": assistant.id,
                        "name": assistant.name,
                        "instructions": assistant.instructions,
                        "status": assistant.status,
                        "capability_count": len(capabilities),
                        "created_at": assistant.created_at.isoformat(),
                    }
                }
            })

    async def _handle_activate_assistant(self, connection_id: str, message: dict) -> None:
        """Handle assistant activation request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        assistant_id = payload.get("assistant_id")

        if not assistant_id:
            await self._send_error(
                connection_id,
                "Missing assistant_id",
                "MISSING_ASSISTANT_ID",
                correlation_id=message["id"]
            )
            return

        with get_db_session() as db:
            # Get assistant
            assistant = db.query(Assistant).filter(
                Assistant.id == assistant_id,
                Assistant.deleted_at.is_(None)
            ).first()

            if not assistant:
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} not found",
                    "ASSISTANT_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            # Deactivate all other assistants
            db.query(Assistant).filter(
                Assistant.deleted_at.is_(None)
            ).update({"status": "inactive"})

            # Activate this assistant
            assistant.status = "active"
            db.commit()
            db.refresh(assistant)

            # Send success response
            await self.connection_manager.send_message(connection_id, {
                "type": "assistant_updated",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "id": assistant.id,
                    "status": assistant.status,
                    "updated_at": assistant.updated_at.isoformat(),
                }
            })

    async def _handle_deactivate_assistant(self, connection_id: str, message: dict) -> None:
        """Handle assistant deactivation request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        assistant_id = payload.get("assistant_id")

        if not assistant_id:
            await self._send_error(
                connection_id,
                "Missing assistant_id",
                "MISSING_ASSISTANT_ID",
                correlation_id=message["id"]
            )
            return

        with get_db_session() as db:
            # Get assistant
            assistant = db.query(Assistant).filter(
                Assistant.id == assistant_id,
                Assistant.deleted_at.is_(None)
            ).first()

            if not assistant:
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} not found",
                    "ASSISTANT_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            # Deactivate assistant
            assistant.status = "inactive"
            db.commit()
            db.refresh(assistant)

            # Send success response
            await self.connection_manager.send_message(connection_id, {
                "type": "assistant_updated",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "id": assistant.id,
                    "status": assistant.status,
                    "updated_at": assistant.updated_at.isoformat(),
                }
            })

    async def _handle_delete_assistant(self, connection_id: str, message: dict) -> None:
        """Handle assistant deletion request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        assistant_id = payload.get("assistant_id")

        if not assistant_id:
            await self._send_error(
                connection_id,
                "Missing assistant_id",
                "MISSING_ASSISTANT_ID",
                correlation_id=message["id"]
            )
            return

        with get_db_session() as db:
            # Get assistant
            assistant = db.query(Assistant).filter(
                Assistant.id == assistant_id,
                Assistant.deleted_at.is_(None)
            ).first()

            if not assistant:
                await self._send_error(
                    connection_id,
                    f"Assistant {assistant_id} not found",
                    "ASSISTANT_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            # Soft delete assistant (sets deleted_at timestamp)
            assistant.deleted_at = datetime.utcnow()

            # Cascade soft delete sessions
            db.query(DBSession).filter(
                DBSession.assistant_id == assistant_id,
                DBSession.archived_at.is_(None)
            ).update({"archived_at": datetime.utcnow()})

            db.commit()

            # Send success response
            await self.connection_manager.send_message(connection_id, {
                "type": "assistant_deleted",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "id": assistant.id,
                    "deleted_at": assistant.deleted_at.isoformat(),
                }
            })

    async def _handle_get_queue_status(self, connection_id: str, message: dict) -> None:
        """Handle queue status request."""
        # TODO: Implement in Phase 6 (User Story 4)
        # Will return current queue state
        await self._send_ack(connection_id, message["id"])

    async def _handle_archive_session(self, connection_id: str, message: dict) -> None:
        """Handle session archiving request."""
        await self._send_ack(connection_id, message["id"])

        payload = message.get("payload", {})
        session_id = payload.get("session_id")

        if not session_id:
            await self._send_error(
                connection_id,
                "Missing session_id",
                "MISSING_SESSION_ID",
                correlation_id=message["id"]
            )
            return

        with get_db_session() as db:
            # Get session
            session = db.query(DBSession).filter(
                DBSession.id == session_id,
                DBSession.archived_at.is_(None)
            ).first()

            if not session:
                await self._send_error(
                    connection_id,
                    f"Session {session_id} not found or already archived",
                    "SESSION_NOT_FOUND",
                    correlation_id=message["id"]
                )
                return

            # Archive session
            session.archived_at = datetime.utcnow()
            db.commit()
            db.refresh(session)

            # Send success response
            await self.connection_manager.send_message(connection_id, {
                "type": "session_archived",
                "id": str(uuid4()),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "correlation_id": message["id"],
                "payload": {
                    "id": session.id,
                    "archived_at": session.archived_at.isoformat(),
                }
            })

    async def _handle_ping(self, connection_id: str, message: dict) -> None:
        """Handle heartbeat ping."""
        # Update heartbeat timestamp
        await self.connection_manager.update_heartbeat(connection_id)

        # Send pong response
        await self._send_pong(connection_id, message["id"])

    # ========== Helper Methods ==========

    async def _send_ack(self, connection_id: str, correlation_id: str) -> None:
        """Send acknowledgment message."""
        await self.connection_manager.send_message(connection_id, {
            "type": "ack",
            "id": str(uuid4()),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "correlation_id": correlation_id
        })

    async def _send_pong(self, connection_id: str, correlation_id: str) -> None:
        """Send pong response to ping."""
        await self.connection_manager.send_message(connection_id, {
            "type": "pong",
            "id": str(uuid4()),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "correlation_id": correlation_id
        })

    async def _send_error(
        self,
        connection_id: str,
        message: str,
        code: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """Send error message to client."""
        error_msg = {
            "type": "error",
            "id": str(uuid4()),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "payload": {
                "message": message,
                "code": code
            }
        }

        if correlation_id:
            error_msg["correlation_id"] = correlation_id

        await self.connection_manager.send_message(connection_id, error_msg)

    async def send_status_update(
        self,
        connection_id: str,
        status: str,
        message: str,
        correlation_id: str
    ) -> None:
        """
        Send status update to client.

        Args:
            connection_id: Target connection
            status: Status type (queued, executing, completed, failed)
            message: Status message
            correlation_id: Original command ID
        """
        await self.connection_manager.send_message(connection_id, {
            "type": "status_update",
            "id": str(uuid4()),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "correlation_id": correlation_id,
            "payload": {
                "status": status,
                "message": message
            }
        })

    async def send_tool_execution(
        self,
        connection_id: str,
        tool: str,
        params: dict,
        correlation_id: str,
        timeout_ms: int = 30000
    ) -> None:
        """
        Request tool execution from client.

        Args:
            connection_id: Target connection
            tool: Tool name
            params: Tool parameters
            correlation_id: Command ID
            timeout_ms: Execution timeout
        """
        await self.connection_manager.send_message(connection_id, {
            "type": "tool_execution",
            "id": str(uuid4()),
            "timestamp": int(datetime.utcnow().timestamp() * 1000),
            "correlation_id": correlation_id,
            "payload": {
                "tool": tool,
                "params": params,
                "timeout_ms": timeout_ms
            }
        })


# Global message handler instance
_message_handler: MessageHandler = None


def get_message_handler() -> MessageHandler:
    """
    Get or create the global message handler instance.

    Returns:
        MessageHandler instance
    """
    global _message_handler
    if _message_handler is None:
        from app.websocket.manager import get_connection_manager
        _message_handler = MessageHandler(get_connection_manager())
    return _message_handler
