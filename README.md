# Agentra

**Autonomous Browser Intelligence Platform**

Agentra is a powerful browser extension-based AI agent system that brings autonomous intelligence directly into your Chrome browser. Control your browser with natural language, create dynamic sub-agents on the fly, and automate complex web workflows—all through a simple sidebar interface.

---

## Overview

Agentra combines the power of OpenAI's Agents SDK with browser automation to create an intelligent assistant that lives in your browser. Unlike traditional browser automation tools, Agentra understands context, reasons about tasks, and can dynamically spawn specialized sub-agents to handle complex workflows.

The system consists of a Chrome extension frontend that provides a chat interface and DOM control capabilities, paired with a Python backend that handles agent orchestration, tool execution, and persistent memory.

## Features

- **Natural Language Browser Control** - Navigate, click, type, extract data, and scroll using conversational commands
- **Sidebar Chat Interface** - Clean, accessible UI built with React and shadcn/ui components
- **Dynamic Sub-Agent Creation** - Spawn specialized agents at runtime with custom tools and permissions using `/sub_agents create`
- **Agent Registry System** - Centralized management of all agents with metadata, capabilities, and lifecycle control
- **Modular Tool System** - Extensible architecture for adding new browser and backend capabilities
- **Persistent Memory** - SQLite-based storage for sessions, agents, and conversation history
- **Real-Time Communication** - WebSocket-powered bidirectional messaging between extension and backend
- **Tool Permission Isolation** - Fine-grained control over what each agent can access and execute
- **Multi-Agent Architecture** - Coordinate multiple specialized agents working together on complex tasks

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Chrome Browser                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Agentra Extension (Plasmo + React)                   │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │  │
│  │  │   Sidebar   │  │   Content    │  │  Background  │ │  │
│  │  │   Chat UI   │  │   Script     │  │   Script     │ │  │
│  │  │  (Zustand)  │  │ (DOM Control)│  │  (Bridge)    │ │  │
│  │  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘ │  │
│  └─────────┼────────────────┼──────────────────┼─────────┘  │
└────────────┼────────────────┼──────────────────┼────────────┘
             │                │                  │
             └────────────────┴──────────────────┘
                              │
                         WebSocket
                              │
┌─────────────────────────────┼────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────────────────┴───────────────────────────┐   │
│  │           WebSocket Handler                          │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │      OpenAI Agents SDK Runtime                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │   Main     │  │  Sub-Agent │  │  Sub-Agent │     │   │
│  │  │   Agent    │  │     #1     │  │     #2     │     │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘     │   │
│  └────────┼───────────────┼───────────────┼────────────┘   │
│           │               │               │                 │
│  ┌────────┴───────────────┴───────────────┴────────────┐   │
│  │            Agent Registry & Tool System             │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │   SQLite Database (Sessions, Agents, Memory)        │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend (Browser Extension)
- **Plasmo** - Modern browser extension framework
- **React** - UI component library
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first styling
- **shadcn/ui** - High-quality UI components
- **Chrome Extension API** - Browser integration
- **Zustand** - Lightweight state management

### Backend
- **Python 3.11+** - Core runtime
- **FastAPI** - High-performance web framework
- **OpenAI Agents SDK** - Agent orchestration and reasoning
- **OpenAI Router Provider** - Model access and routing
- **SQLite** - Persistent storage
- **SQLAlchemy** - Database ORM
- **WebSocket** - Real-time communication

### Memory Layer
- **SQLite** - Sessions, agents, and conversation history
- **FAISS / ChromaDB** - Optional vector memory for semantic search

## Installation

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm/pnpm
- Chrome browser
- OpenAI API key

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agentra.git
cd agentra
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Create a `.env` file in the `backend` directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./agentra.db
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8000
LOG_LEVEL=INFO
```

5. Initialize the database:
```bash
python -m app.db.init_db
```

### Extension Setup

1. Install frontend dependencies:
```bash
cd extension
pnpm install  # or npm install
```

2. Build the extension:
```bash
pnpm build  # or npm run build
```

3. Load the extension in Chrome:
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `extension/build/chrome-mv3-prod` directory

## Running the System

### Start the Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### Use the Extension

1. Click the Agentra icon in your Chrome toolbar
2. The sidebar will open with the chat interface
3. Start interacting with natural language commands

Example commands:
```
"Navigate to github.com"
"Click the sign in button"
"Extract all repository names from this page"
"Scroll down to load more content"
```

## Project Structure

```
agentra/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py
│   │   │   ├── main_agent.py
│   │   │   └── registry.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── browser_tools.py
│   │   │   ├── extraction_tools.py
│   │   │   └── navigation_tools.py
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── websocket/
│   │   │   ├── __init__.py
│   │   │   ├── handler.py
│   │   │   └── manager.py
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
├── extension/
│   ├── src/
│   │   ├── background/
│   │   │   └── index.ts
│   │   ├── content/
│   │   │   └── index.tsx
│   │   ├── sidepanel/
│   │   │   ├── index.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── AgentList.tsx
│   │   ├── components/
│   │   │   └── ui/
│   │   ├── lib/
│   │   │   ├── websocket.ts
│   │   │   └── store.ts
│   │   └── types/
│   │       └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
└── README.md
```

## Dynamic Sub-Agents

### How It Works

Agentra's most powerful feature is the ability to create specialized sub-agents at runtime. These agents are spawned dynamically based on your needs and can have custom tools, permissions, and instructions.

When you create a sub-agent:
1. The main agent receives your `/sub_agents create` command
2. A new agent instance is registered in the Agent Registry
3. The sub-agent is configured with specified tools and permissions
4. The agent becomes available for task delegation
5. The sub-agent can communicate back through the main agent

### Creating a Sub-Agent

Use the `/sub_agents create` command in the chat interface:

```
/sub_agents create name="DataExtractor" role="Extract structured data from web pages" tools=["extract_text", "extract_links", "extract_tables"] permissions=["read_dom"]
```

### Example: Research Assistant Sub-Agent

```python
# Backend: Creating a sub-agent programmatically
from app.agents.registry import AgentRegistry
from app.agents.base_agent import BaseAgent
from app.tools.browser_tools import extract_text, extract_links

registry = AgentRegistry()

research_agent = BaseAgent(
    name="ResearchAssistant",
    role="Gather and summarize information from multiple sources",
    instructions="""
    You are a research assistant that:
    1. Navigates to specified URLs
    2. Extracts relevant information
    3. Summarizes findings
    4. Compiles results into structured format
    """,
    tools=[extract_text, extract_links, "navigate", "scroll"],
    permissions=["read_dom", "navigate", "extract"]
)

agent_id = registry.register(research_agent)
print(f"Research agent created with ID: {agent_id}")
```

### Sub-Agent Communication

Sub-agents can communicate with the main agent and each other:

```typescript
// Extension: Handling sub-agent messages
interface SubAgentMessage {
  agentId: string;
  agentName: string;
  action: string;
  payload: any;
  timestamp: number;
}

const handleSubAgentMessage = (message: SubAgentMessage) => {
  console.log(`Sub-agent ${message.agentName} performed: ${message.action}`);
  
  // Update UI with sub-agent activity
  updateAgentStatus(message.agentId, message.action);
  
  // Forward results to main agent if needed
  if (message.action === "task_complete") {
    sendToMainAgent({
      type: "sub_agent_result",
      data: message.payload
    });
  }
};
```

## Tool System

### Available Tools

Agentra provides a comprehensive set of tools for browser automation:

**Navigation Tools:**
- `navigate(url)` - Navigate to a URL
- `go_back()` - Go back in history
- `go_forward()` - Go forward in history
- `refresh()` - Refresh current page

**Interaction Tools:**
- `click(selector)` - Click an element
- `type_text(selector, text)` - Type into an input field
- `scroll(direction, amount)` - Scroll the page
- `hover(selector)` - Hover over an element

**Extraction Tools:**
- `extract_text(selector)` - Extract text content
- `extract_links()` - Get all links on page
- `extract_tables()` - Extract table data
- `screenshot(selector?)` - Capture screenshot

### Creating Custom Tools

```python
# backend/app/tools/custom_tools.py
from typing import Dict, Any
from app.tools.base import Tool

class CustomAnalysisTool(Tool):
    name = "analyze_sentiment"
    description = "Analyze sentiment of text content on the page"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "selector": {
                "type": "string",
                "description": "CSS selector for text to analyze"
            }
        }
    
    async def execute(self, selector: str) -> Dict[str, Any]:
        # Extract text from page
        text = await self.extract_text(selector)
        
        # Perform sentiment analysis
        sentiment = self.analyze(text)
        
        return {
            "selector": selector,
            "text": text[:100],
            "sentiment": sentiment,
            "confidence": 0.95
        }
    
    def analyze(self, text: str) -> str:
        # Your sentiment analysis logic here
        return "positive"

# Register the tool
from app.tools.registry import tool_registry
tool_registry.register(CustomAnalysisTool())
```

### Tool Execution Flow

```typescript
// Extension: Tool execution from frontend
const executeTool = async (toolName: string, params: any) => {
  // Send tool execution request via WebSocket
  const message = {
    type: "tool_execution",
    tool: toolName,
    parameters: params,
    timestamp: Date.now()
  };
  
  ws.send(JSON.stringify(message));
  
  // Wait for response
  return new Promise((resolve) => {
    const handler = (event: MessageEvent) => {
      const response = JSON.parse(event.data);
      if (response.type === "tool_result" && response.tool === toolName) {
        ws.removeEventListener("message", handler);
        resolve(response.result);
      }
    };
    ws.addEventListener("message", handler);
  });
};

// Usage
const links = await executeTool("extract_links", {});
console.log(`Found ${links.length} links on the page`);
```

## Agent Architecture

### Agent Registry

The Agent Registry is the central hub for managing all agents in the system:

```python
# backend/app/agents/registry.py
from typing import Dict, Optional, List
from datetime import datetime
from app.agents.base_agent import BaseAgent
from app.db.models import Agent as AgentModel
from app.db.session import get_db

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._db = get_db()
    
    def register(self, agent: BaseAgent) -> str:
        """Register a new agent and persist to database"""
        agent_id = agent.id
        self._agents[agent_id] = agent
        
        # Persist to database
        db_agent = AgentModel(
            id=agent_id,
            name=agent.name,
            role=agent.role,
            tools=agent.tools,
            permissions=agent.permissions,
            created_at=datetime.utcnow(),
            status="active"
        )
        self._db.add(db_agent)
        self._db.commit()
        
        return agent_id
    
    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """Retrieve an agent by ID"""
        return self._agents.get(agent_id)
    
    def list_active(self) -> List[BaseAgent]:
        """List all active agents"""
        return [
            agent for agent in self._agents.values()
            if agent.status == "active"
        ]
    
    def deactivate(self, agent_id: str) -> bool:
        """Deactivate an agent"""
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = "inactive"
            # Update database
            db_agent = self._db.query(AgentModel).filter_by(id=agent_id).first()
            if db_agent:
                db_agent.status = "inactive"
                self._db.commit()
            return True
        return False

# Global registry instance
registry = AgentRegistry()
```

### Base Agent Class

```python
# backend/app/agents/base_agent.py
from typing import List, Dict, Any, Optional
import uuid
from openai import OpenAI

class BaseAgent:
    def __init__(
        self,
        name: str,
        role: str,
        instructions: str,
        tools: List[str],
        permissions: List[str],
        model: str = "gpt-4-turbo-preview"
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.instructions = instructions
        self.tools = tools
        self.permissions = permissions
        self.model = model
        self.status = "active"
        self.client = OpenAI()
        self.thread_id: Optional[str] = None
    
    async def initialize(self):
        """Initialize the agent with OpenAI Agents SDK"""
        # Create assistant
        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            model=self.model,
            tools=[{"type": "function", "function": tool} for tool in self.tools]
        )
        
        # Create thread
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message and return response"""
        if not self.thread_id:
            await self.initialize()
        
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=message
        )
        
        # Run assistant
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant.id
        )
        
        # Wait for completion and handle tool calls
        return await self._handle_run(run.id)
    
    async def _handle_run(self, run_id: str) -> Dict[str, Any]:
        """Handle run execution and tool calls"""
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run_id
            )
            
            if run.status == "completed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread_id
                )
                return {
                    "status": "success",
                    "response": messages.data[0].content[0].text.value
                }
            
            elif run.status == "requires_action":
                # Handle tool calls
                tool_outputs = await self._execute_tools(
                    run.required_action.submit_tool_outputs.tool_calls
                )
                
                self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs
                )
            
            elif run.status in ["failed", "cancelled", "expired"]:
                return {
                    "status": "error",
                    "error": f"Run {run.status}"
                }
    
    async def _execute_tools(self, tool_calls) -> List[Dict]:
        """Execute requested tools"""
        from app.tools.registry import tool_registry
        
        outputs = []
        for tool_call in tool_calls:
            tool = tool_registry.get(tool_call.function.name)
            if tool and tool.name in self.tools:
                result = await tool.execute(**tool_call.function.arguments)
                outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": str(result)
                })
        
        return outputs
```

## Development Roadmap

### Current Version (v0.1.0)
- ✅ Core browser automation tools
- ✅ WebSocket communication
- ✅ Basic agent system
- ✅ SQLite persistence
- ✅ Dynamic sub-agent creation

### Upcoming Features

**v0.2.0 - Enhanced Intelligence**
- Vector memory integration (FAISS/ChromaDB)
- Long-term memory and context retention
- Multi-modal support (images, PDFs)
- Advanced extraction capabilities

**v0.3.0 - Collaboration**
- Multi-agent coordination protocols
- Shared memory between agents
- Agent-to-agent communication
- Workflow orchestration

**v0.4.0 - Enterprise Features**
- User authentication and authorization
- Team collaboration features
- Agent marketplace
- Custom model support (Anthropic, local models)
- Audit logging and compliance

**v0.5.0 - Advanced Automation**
- Visual workflow builder
- Scheduled agent tasks
- Browser recording and playback
- Integration with external APIs
- Mobile browser support

## Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript strict mode
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

### Code Style

**Python:**
```python
# Use type hints
def process_message(message: str, agent_id: str) -> Dict[str, Any]:
    pass

# Use docstrings
def create_agent(name: str) -> BaseAgent:
    """
    Create a new agent instance.
    
    Args:
        name: The name of the agent
        
    Returns:
        A configured BaseAgent instance
    """
    pass
```

**TypeScript:**
```typescript
// Use interfaces for type safety
interface AgentConfig {
  name: string;
  role: string;
  tools: string[];
}

// Use async/await
const createAgent = async (config: AgentConfig): Promise<Agent> => {
  // Implementation
};
```

### Reporting Issues

Found a bug or have a feature request? Please open an issue with:
- Clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Screenshots if applicable
- Environment details (OS, Chrome version, etc.)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by the Agentra team**

[Documentation](https://docs.agentra.dev) • [Discord Community](https://discord.gg/agentra) • [Twitter](https://twitter.com/agentra_ai)
