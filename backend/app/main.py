"""
FastAPI application entry point for BrowserMind backend.
Configures CORS, WebSocket endpoint, startup/shutdown events, and health checks.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.cleanup import start_cleanup_job, stop_cleanup_job
from app.db.encryption import init_encryption
from app.db.session import close_database, init_database
from app.tools import browser_tools, extraction_tools  # Import to register tools
from app.websocket.handler import get_message_handler
from app.websocket.manager import get_connection_manager
from app.websocket.protocol import get_protocol_info
from app.websocket.rate_limiter import get_rate_limiter
from app.websocket.queue import get_command_queue
from app.agents.agent_sdk_orchestrator import get_agent_sdk_orchestrator
from app.config.openrouter import get_llm_config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("Starting BrowserMind backend...")

    # Initialize encryption
    init_encryption(settings.database_encryption_key)
    print("[OK] Encryption initialized")

    # Initialize database
    init_database()
    print("[OK] Database initialized")

    # Initialize LLM configuration
    llm_config = get_llm_config()
    print(f"[OK] LLM provider: {llm_config.llm_provider}")
    print(f"[OK] Model: {llm_config.default_model if llm_config.llm_provider == 'openrouter' else 'gpt-4-turbo-preview'}")

    # Initialize Agent SDK orchestrator with multi-agent handoffs
    orchestrator = get_agent_sdk_orchestrator()
    print("[OK] OpenAI Agent SDK orchestrator initialized")
    print("[OK] Multi-agent system: Coordinator + 3 specialists (Navigation, Extraction, Interaction)")

    # Initialize command queue
    command_queue = get_command_queue()
    await command_queue.start_timeout_monitor()
    print("[OK] Command queue initialized")

    # Start connection manager heartbeat monitor
    connection_manager = get_connection_manager()
    await connection_manager.start_heartbeat_monitor()
    print("[OK] WebSocket heartbeat monitor started")

    # Start cleanup job
    if settings.enable_cleanup_job:
        asyncio.create_task(start_cleanup_job())
        print("[OK] Cleanup job scheduled")

    print(f"[OK] BrowserMind backend ready on {settings.host}:{settings.port}")

    yield

    # Shutdown
    print("Shutting down BrowserMind backend...")

    # Stop cleanup job
    await stop_cleanup_job()

    # Stop heartbeat monitor
    await connection_manager.stop_heartbeat_monitor()

    # Close database
    close_database()

    print("[OK] Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="BrowserMind Backend",
    description="Autonomous browser intelligence platform with multi-agent system",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns service status and basic metrics.
    """
    connection_manager = get_connection_manager()

    return {
        "status": "healthy",
        "version": "0.1.0",
        "protocol_version": get_protocol_info()["version"],
        "connections": {
            "active": connection_manager.get_connection_count(),
            "max": settings.ws_max_connections
        },
        "database": {
            "url": settings.database_url.replace(settings.database_encryption_key, "***")
        }
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "BrowserMind Backend",
        "version": "0.1.0",
        "protocol": get_protocol_info(),
        "endpoints": {
            "health": "/health",
            "websocket": "/ws",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional communication.
    Handles connection lifecycle, message routing, and rate limiting.
    """
    connection_manager = get_connection_manager()
    message_handler = get_message_handler()
    rate_limiter = get_rate_limiter()

    connection_id = None

    try:
        # Accept connection and assign ID
        connection_id = await connection_manager.connect(websocket)

        # Send welcome message with protocol info
        await connection_manager.send_message(connection_id, {
            "type": "connected",
            "id": connection_id,
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
            "payload": get_protocol_info()
        })

        # Message loop
        while True:
            # Receive message
            message = await websocket.receive_json()

            # Check rate limit
            allowed, retry_after = rate_limiter.check_rate_limit(connection_id)
            if not allowed:
                await connection_manager.send_message(connection_id, {
                    "type": "error",
                    "id": connection_id,
                    "timestamp": int(asyncio.get_event_loop().time() * 1000),
                    "payload": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Retry after {retry_after} seconds.",
                        "retry_after": retry_after
                    }
                })
                continue

            # Handle message
            await message_handler.handle_message(connection_id, message)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        print(f"WebSocket error for {connection_id}: {e}")

    finally:
        # Clean up connection
        if connection_id:
            await connection_manager.disconnect(connection_id)
            rate_limiter.reset(connection_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    )
