@echo off
REM BrowserMind Backend Startup Script for Windows

echo =========================================
echo BrowserMind Backend Startup
echo =========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run: uv venv
    exit /b 1
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file with required configuration:
    echo   copy .env.example .env
    echo.
    echo Then edit .env and set:
    echo   - OPENROUTER_API_KEY or OPENAI_API_KEY
    echo   - DATABASE_ENCRYPTION_KEY
    echo   - SECRET_KEY
    echo.
    pause
    exit /b 1
)

REM Verify components
echo [INFO] Verifying components...
python -c "from app.agents.assistant_agent import AssistantAgent; from app.agents.openai_orchestrator import get_orchestrator; from app.tools.base import get_tool_registry; print('[OK] All components loaded')" 2>&1 | findstr /C:"[OK]" /C:"Error"

echo.
echo [INFO] Starting BrowserMind backend...
echo    Server: http://0.0.0.0:8000
echo    Health: http://0.0.0.0:8000/health
echo    Docs:   http://0.0.0.0:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

REM Start server
python -m app.main
