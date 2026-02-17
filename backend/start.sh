#!/bin/bash
# BrowserMind Backend Startup Script

set -e

echo "========================================="
echo "BrowserMind Backend Startup"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: uv venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "Please create .env file with required configuration:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env and set:"
    echo "  - OPENROUTER_API_KEY or OPENAI_API_KEY"
    echo "  - DATABASE_ENCRYPTION_KEY"
    echo "  - SECRET_KEY"
    echo ""
    exit 1
fi

# Check for API key
if ! grep -q "OPENROUTER_API_KEY=sk-or-v1-" .env && ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  Warning: No API key found in .env"
    echo ""
    echo "Please set one of:"
    echo "  - OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY"
    echo "  - OPENAI_API_KEY=sk-YOUR_KEY"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Verify components
echo "🔍 Verifying components..."
python -c "
from app.agents.assistant_agent import AssistantAgent
from app.agents.openai_orchestrator import get_orchestrator
from app.tools.base import get_tool_registry
print('[OK] All components loaded')
" 2>&1 | grep -E '\[OK\]|Error' || true

echo ""
echo "🚀 Starting BrowserMind backend..."
echo "   Server: http://0.0.0.0:8000"
echo "   Health: http://0.0.0.0:8000/health"
echo "   Docs:   http://0.0.0.0:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
python -m app.main
