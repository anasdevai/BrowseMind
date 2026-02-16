"""
WebSocket connection manager.
Handles client connections, heartbeat monitoring, and message broadcasting.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings


class ConnectionManager:
    """
    Manages WebSocket connections with heartbeat monitoring.
    Supports connection tracking, broadcasting, and automatic cleanup.
    """

    def __init__(self):
        # Active connections: connection_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # Connection metadata: connection_id -> metadata
        self.connection_metadata: Dict[str, dict] = {}

        # Heartbeat tracking: connection_id -> last_heartbeat_time
        self.last_heartbeat: Dict[str, datetime] = {}

        # Heartbeat monitor task
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept a new WebSocket connection and assign it a unique ID.

        Args:
            websocket: FastAPI WebSocket instance

        Returns:
            Unique connection ID

        Raises:
            RuntimeError: If max connections exceeded
        """
        # Check connection limit
        if len(self.active_connections) >= settings.ws_max_connections:
            await websocket.close(code=1008, reason="Max connections exceeded")
            raise RuntimeError("Maximum WebSocket connections exceeded")

        # Accept connection
        await websocket.accept()

        # Generate unique connection ID
        connection_id = str(uuid4())

        # Store connection
        self.active_connections[connection_id] = websocket
        self.connection_metadata[connection_id] = {
            "connected_at": datetime.utcnow(),
            "message_count": 0,
            "last_message_at": None
        }
        self.last_heartbeat[connection_id] = datetime.utcnow()

        print(f"WebSocket connected: {connection_id} (total: {len(self.active_connections)})")
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and clean up a WebSocket connection.

        Args:
            connection_id: Connection ID to disconnect
        """
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]

            # Close WebSocket if still open
            try:
                await websocket.close()
            except Exception:
                pass  # Already closed

            # Clean up tracking data
            del self.active_connections[connection_id]
            del self.connection_metadata[connection_id]
            del self.last_heartbeat[connection_id]

            print(f"WebSocket disconnected: {connection_id} (remaining: {len(self.active_connections)})")

    async def send_message(self, connection_id: str, message: dict) -> None:
        """
        Send a JSON message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message dictionary to send

        Raises:
            KeyError: If connection not found
        """
        if connection_id not in self.active_connections:
            raise KeyError(f"Connection {connection_id} not found")

        websocket = self.active_connections[connection_id]
        await websocket.send_json(message)

        # Update metadata
        metadata = self.connection_metadata[connection_id]
        metadata["message_count"] += 1
        metadata["last_message_at"] = datetime.utcnow()

    async def broadcast(self, message: dict, exclude: Optional[Set[str]] = None) -> None:
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
            exclude: Optional set of connection IDs to exclude
        """
        exclude = exclude or set()

        for connection_id, websocket in list(self.active_connections.items()):
            if connection_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to {connection_id}: {e}")
                    # Connection may be dead, will be cleaned up by heartbeat monitor

    async def update_heartbeat(self, connection_id: str) -> None:
        """
        Update the last heartbeat time for a connection.

        Args:
            connection_id: Connection ID
        """
        if connection_id in self.last_heartbeat:
            self.last_heartbeat[connection_id] = datetime.utcnow()

    async def start_heartbeat_monitor(self) -> None:
        """
        Start the heartbeat monitoring task.
        Disconnects clients that haven't sent heartbeat within timeout.
        """
        if self._is_running:
            return

        self._is_running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())
        print("Heartbeat monitor started")

    async def stop_heartbeat_monitor(self) -> None:
        """Stop the heartbeat monitoring task."""
        self._is_running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        print("Heartbeat monitor stopped")

    async def _heartbeat_monitor_loop(self) -> None:
        """
        Internal heartbeat monitoring loop.
        Checks for stale connections every 10 seconds.
        """
        while self._is_running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                await self._check_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in heartbeat monitor: {e}")

    async def _check_stale_connections(self) -> None:
        """
        Check for and disconnect stale connections.
        Connections are stale if no heartbeat received within timeout period.
        """
        now = datetime.utcnow()
        timeout_seconds = settings.ws_heartbeat_interval * 2  # 2x heartbeat interval

        stale_connections = []
        for connection_id, last_beat in self.last_heartbeat.items():
            elapsed = (now - last_beat).total_seconds()
            if elapsed > timeout_seconds:
                stale_connections.append(connection_id)

        # Disconnect stale connections
        for connection_id in stale_connections:
            print(f"Disconnecting stale connection: {connection_id}")
            await self.disconnect(connection_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_connection_info(self, connection_id: str) -> Optional[dict]:
        """
        Get metadata for a specific connection.

        Args:
            connection_id: Connection ID

        Returns:
            Connection metadata or None if not found
        """
        return self.connection_metadata.get(connection_id)

    def get_all_connections(self) -> Dict[str, dict]:
        """
        Get metadata for all active connections.

        Returns:
            Dictionary mapping connection IDs to metadata
        """
        return self.connection_metadata.copy()


# Global connection manager instance
_connection_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    """
    Get or create the global connection manager instance.

    Returns:
        ConnectionManager instance
    """
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
