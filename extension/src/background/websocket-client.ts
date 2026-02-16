/**
 * WebSocket client for backend communication.
 * Handles connection lifecycle, auto-reconnect, heartbeat, and message routing.
 */
import type {
  WSMessage,
  ProtocolInfo,
  ConnectionStatus as WSConnectionStatus,
} from "~/types/websocket";
import { ConnectionStatus } from "~/types/websocket";

type MessageHandler = (message: WSMessage) => void | Promise<void>;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000; // Start at 1 second
  private maxReconnectDelay = 30000; // Max 30 seconds
  private heartbeatInterval: number | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionId: string | null = null;
  private protocolInfo: ProtocolInfo | null = null;

  constructor(url: string) {
    this.url = url;
  }

  /**
   * Connect to WebSocket server.
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("WebSocket already connected");
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);

      console.log("WebSocket connecting...");
    } catch (error) {
      console.error("WebSocket connection error:", error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server.
   */
  disconnect(): void {
    this.stopHeartbeat();
    this.clearReconnectTimer();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.connectionId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Send a message to the server.
   */
  send(message: WSMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected, cannot send message");
      throw new Error("WebSocket not connected");
    }

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Register a message handler.
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    // Return unsubscribe function
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Get connection status.
   */
  getStatus(): ConnectionStatus {
    if (!this.ws) return ConnectionStatus.DISCONNECTED;

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return this.reconnectAttempts > 0
          ? ConnectionStatus.RECONNECTING
          : ConnectionStatus.CONNECTING;
      case WebSocket.OPEN:
        return ConnectionStatus.CONNECTED;
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return ConnectionStatus.DISCONNECTED;
      default:
        return ConnectionStatus.DISCONNECTED;
    }
  }

  /**
   * Get connection ID.
   */
  getConnectionId(): string | null {
    return this.connectionId;
  }

  /**
   * Get protocol info.
   */
  getProtocolInfo(): ProtocolInfo | null {
    return this.protocolInfo;
  }

  // Private methods

  private handleOpen(): void {
    console.log("WebSocket connected");
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSMessage = JSON.parse(event.data);

      // Handle special messages
      if (message.type === "connected") {
        this.connectionId = message.id;
        this.protocolInfo = message.payload as ProtocolInfo;
        console.log("WebSocket handshake complete:", this.connectionId);

        // Start heartbeat
        if (this.protocolInfo?.timeouts?.heartbeat_interval_seconds) {
          this.startHeartbeat(
            this.protocolInfo.timeouts.heartbeat_interval_seconds * 1000
          );
        }
      } else if (message.type === "pong") {
        // Heartbeat response received
        console.debug("Heartbeat pong received");
      }

      // Notify all handlers
      this.messageHandlers.forEach((handler) => {
        try {
          handler(message);
        } catch (error) {
          console.error("Error in message handler:", error);
        }
      });
    } catch (error) {
      console.error("Error parsing WebSocket message:", error);
    }
  }

  private handleError(event: Event): void {
    console.error("WebSocket error:", event);
  }

  private handleClose(event: CloseEvent): void {
    console.log("WebSocket closed:", event.code, event.reason);

    this.stopHeartbeat();
    this.connectionId = null;
    this.protocolInfo = null;

    // Attempt reconnect if not a normal closure
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("Max reconnect attempts reached");
      return;
    }

    this.clearReconnectTimer();

    console.log(
      `Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 30s (max)
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2,
      this.maxReconnectDelay
    );
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private startHeartbeat(interval: number): void {
    this.stopHeartbeat();

    this.heartbeatInterval = interval;
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, interval);

    console.log(`Heartbeat started (interval: ${interval}ms)`);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private sendHeartbeat(): void {
    try {
      this.send({
        type: "ping",
        id: crypto.randomUUID(),
        timestamp: Date.now(),
        payload: {},
      });
    } catch (error) {
      console.error("Error sending heartbeat:", error);
    }
  }
}
