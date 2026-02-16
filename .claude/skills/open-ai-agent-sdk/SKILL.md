---
name: openai-agent-sdk
description: Build AI agents using OpenAI's Agent SDK (Swarm). Use when creating multi-agent systems, orchestrating AI workflows, building agentic applications, or when user mentions OpenAI agents, Swarm, agent handoffs, or tool calling.
---

# OpenAI Agent SDK (Swarm) Skill

When building AI agents with OpenAI's Swarm framework, follow these patterns:

## 1. Project Structure

```
agent_project/
├── agents/
│   ├── __init__.py
│   ├── triage_agent.py
│   ├── sales_agent.py
│   └── refund_agent.py
├── tools/
│   ├── __init__.py
│   └── functions.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── main.py
├── requirements.txt
└── .env
```

## 2. Core Setup (main.py)

```python
from swarm import Swarm, Agent
from agents.triage_agent import triage_agent
from dotenv import load_dotenv

load_dotenv()

client = Swarm()

def run_agent_loop():
    """Main agent execution loop"""
    print("Starting Agent System...")
    
    messages = []
    current_agent = triage_agent
    
    while True:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        response = client.run(
            agent=current_agent,
            messages=messages
        )
        
        # Update messages with assistant response
        messages.extend(response.messages)
        
        # Handle agent handoff
        current_agent = response.agent
        
        # Print response
        print(f"Agent: {response.messages[-1]['content']}")

if __name__ == "__main__":
    run_agent_loop()
```

## 3. Agent Definition Pattern

```python
from swarm import Agent

def transfer_to_sales():
    """Transfer conversation to sales agent"""
    return sales_agent

def transfer_to_support():
    """Transfer conversation to support agent"""
    return support_agent

# Define the triage agent
triage_agent = Agent(
    name="Triage Agent",
    instructions="""You are a helpful triage agent. Your job is to:
    1. Greet users warmly
    2. Understand their needs
    3. Route them to the appropriate specialist
    
    Transfer to Sales for: purchases, pricing, demos
    Transfer to Support for: technical issues, refunds, account problems
    """,
    functions=[transfer_to_sales, transfer_to_support],
    model="gpt-4o"
)

# Define specialist agents
sales_agent = Agent(
    name="Sales Agent",
    instructions="""You are a sales specialist. Help customers with:
    - Product information and pricing
    - Demo scheduling
    - Purchase decisions
    Be enthusiastic and helpful!
    """,
    model="gpt-4o"
)

support_agent = Agent(
    name="Support Agent",
    instructions="""You are a technical support specialist. Help customers with:
    - Technical troubleshooting
    - Account issues
    - Refund requests
    Be patient and thorough!
    """,
    functions=[process_refund, check_account_status],
    model="gpt-4o"
)
```

## 4. Tool/Function Definitions (tools/functions.py)

```python
from typing import Dict, Any
import json

def process_refund(order_id: str, reason: str) -> Dict[str, Any]:
    """
    Process a refund for a customer order.
    
    Args:
        order_id: The order ID to refund
        reason: Reason for the refund
    
    Returns:
        Dict containing refund status
    """
    # Implement refund logic
    print(f"Processing refund for order {order_id}")
    
    return {
        "status": "success",
        "order_id": order_id,
        "refund_amount": 99.99,
        "message": f"Refund processed for reason: {reason}"
    }

def check_account_status(user_id: str) -> Dict[str, Any]:
    """
    Check the status of a user account.
    
    Args:
        user_id: The user ID to check
    
    Returns:
        Dict containing account information
    """
    # Implement account check logic
    return {
        "user_id": user_id,
        "status": "active",
        "subscription": "premium",
        "expires": "2024-12-31"
    }

def search_knowledge_base(query: str) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: Search query
    
    Returns:
        Relevant knowledge base articles
    """
    # Implement knowledge base search
    results = [
        "How to reset your password...",
        "Troubleshooting connection issues...",
        "Account security best practices..."
    ]
    return "\n".join(results)

def schedule_meeting(date: str, time: str, attendees: list) -> Dict[str, Any]:
    """
    Schedule a meeting with specified attendees.
    
    Args:
        date: Meeting date (YYYY-MM-DD)
        time: Meeting time (HH:MM)
        attendees: List of attendee emails
    
    Returns:
        Meeting confirmation details
    """
    return {
        "status": "scheduled",
        "date": date,
        "time": time,
        "attendees": attendees,
        "meeting_link": "https://meet.example.com/abc123"
    }
```

## 5. Context Variables Pattern

```python
from swarm import Agent

def get_user_context(context_variables: dict) -> str:
    """Access shared context across agents"""
    user_name = context_variables.get("user_name", "Guest")
    user_tier = context_variables.get("user_tier", "free")
    return f"User: {user_name} (Tier: {user_tier})"

agent_with_context = Agent(
    name="Context-Aware Agent",
    instructions="""Use the user context to personalize responses.
    Check user tier for feature availability.""",
    functions=[get_user_context]
)

# Running with context
response = client.run(
    agent=agent_with_context,
    messages=[{"role": "user", "content": "What features do I have?"}],
    context_variables={
        "user_name": "Alice",
        "user_tier": "premium",
        "account_id": "12345"
    }
)
```

## 6. Multi-Agent Handoff Pattern

```python
from swarm import Agent

def transfer_with_context(target_agent: Agent, summary: str):
    """Transfer to another agent with context"""
    def transfer():
        return target_agent
    transfer.__doc__ = f"Transfer to {target_agent.name}: {summary}"
    return transfer

# Specialized agents with handoff capabilities
customer_service_agent = Agent(
    name="Customer Service",
    instructions="Handle general customer inquiries",
    functions=[
        transfer_with_context(billing_agent, "For billing questions"),
        transfer_with_context(technical_agent, "For technical issues")
    ]
)

billing_agent = Agent(
    name="Billing Specialist",
    instructions="Handle billing, invoices, and payments",
    functions=[process_payment, generate_invoice]
)

technical_agent = Agent(
    name="Technical Support",
    instructions="Handle technical troubleshooting",
    functions=[run_diagnostics, escalate_to_engineering]
)
```

## 7. Streaming Responses

```python
from swarm import Swarm

client = Swarm()

def stream_agent_response():
    """Stream agent responses for better UX"""
    messages = [{"role": "user", "content": "Tell me about your products"}]
    
    stream = client.run(
        agent=sales_agent,
        messages=messages,
        stream=True
    )
    
    for chunk in stream:
        if chunk.get("content"):
            print(chunk["content"], end="", flush=True)
```

## 8. Advanced Agent Patterns

### A. Router Agent (Triage Pattern)
```python
router_agent = Agent(
    name="Router",
    instructions="""You are a router. Analyze the user's request and transfer to:
    - Sales Agent: for purchases, pricing, product info
    - Support Agent: for technical help, bugs, issues
    - Billing Agent: for payments, invoices, refunds
    - Account Agent: for profile, settings, preferences
    
    Only route, don't solve problems yourself.
    """,
    functions=[
        transfer_to_sales,
        transfer_to_support,
        transfer_to_billing,
        transfer_to_account
    ]
)
```

### B. Supervisor Agent Pattern
```python
supervisor_agent = Agent(
    name="Supervisor",
    instructions="""You supervise other agents. You can:
    1. Review agent responses for quality
    2. Escalate complex issues
    3. Override decisions when necessary
    4. Provide final approval
    
    Monitor all interactions and intervene when needed.
    """,
    functions=[approve_action, escalate_issue, override_decision]
)
```

### C. Memory-Enhanced Agent
```python
def save_conversation(user_id: str, summary: str):
    """Save conversation summary to memory"""
    # Store in database or vector store
    pass

def recall_previous_conversations(user_id: str) -> str:
    """Retrieve previous conversation history"""
    # Fetch from database
    return "Previous conversations: ..."

memory_agent = Agent(
    name="Memory Agent",
    instructions="""You remember previous conversations.
    Before responding, recall past interactions.
    After responding, save a summary.""",
    functions=[save_conversation, recall_previous_conversations]
)
```

## 9. Error Handling & Retry Logic

```python
from swarm import Swarm
import time

def run_with_retry(agent, messages, max_retries=3):
    """Run agent with retry logic"""
    client = Swarm()
    
    for attempt in range(max_retries):
        try:
            response = client.run(
                agent=agent,
                messages=messages
            )
            return response
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

# Usage
response = run_with_retry(
    agent=triage_agent,
    messages=[{"role": "user", "content": "Help me"}]
)
```

## 10. Testing Agents

```python
import pytest
from swarm import Swarm
from agents.triage_agent import triage_agent

@pytest.fixture
def client():
    return Swarm()

def test_triage_to_sales(client):
    """Test that triage routes to sales correctly"""
    messages = [
        {"role": "user", "content": "I want to buy your product"}
    ]
    
    response = client.run(
        agent=triage_agent,
        messages=messages
    )
    
    # Check that we transferred to sales agent
    assert response.agent.name == "Sales Agent"
    assert len(response.messages) > 0

def test_refund_function(client):
    """Test the refund processing function"""
    result = process_refund(
        order_id="12345",
        reason="Product defect"
    )
    
    assert result["status"] == "success"
    assert result["order_id"] == "12345"
```

## 11. Configuration Management (config/settings.py)

```python
from pydantic_settings import BaseSettings
from typing import List

class AgentSettings(BaseSettings):
    openai_api_key: str
    model: str = "gpt-4o"
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Agent-specific settings
    enable_streaming: bool = True
    max_handoffs: int = 5
    timeout_seconds: int = 30
    
    # Feature flags
    enable_memory: bool = False
    enable_logging: bool = True
    
    class Config:
        env_file = ".env"

settings = AgentSettings()
```

## Best Practices

1. **Clear Agent Roles**: Each agent should have one clear responsibility
2. **Explicit Instructions**: Write detailed, specific instructions for each agent
3. **Smart Handoffs**: Use transfer functions with descriptive docstrings
4. **Context Management**: Pass relevant context between agents
5. **Tool Documentation**: Write clear docstrings for all functions
6. **Error Handling**: Implement retry logic and graceful degradation
7. **Testing**: Test each agent and function independently
8. **Logging**: Log all agent interactions for debugging
9. **Rate Limiting**: Respect API rate limits with exponential backoff
10. **Security**: Never expose API keys, validate all inputs

## Common Patterns

### Stateful Conversation
```python
class ConversationManager:
    def __init__(self):
        self.messages = []
        self.context = {}
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def run_agent(self, agent):
        client = Swarm()
        response = client.run(
            agent=agent,
            messages=self.messages,
            context_variables=self.context
        )
        self.messages.extend(response.messages)
        return response
```

### Parallel Agent Execution
```python
import asyncio

async def run_agents_parallel(agents, message):
    """Run multiple agents in parallel and aggregate results"""
    client = Swarm()
    
    async def run_single(agent):
        return client.run(
            agent=agent,
            messages=[{"role": "user", "content": message}]
        )
    
    tasks = [run_single(agent) for agent in agents]
    results = await asyncio.gather(*tasks)
    
    return results
```

## Performance Tips

1. **Model Selection**: Use `gpt-4o-mini` for simple routing, `gpt-4o` for complex tasks
2. **Streaming**: Enable streaming for better user experience
3. **Caching**: Cache agent responses for common queries
4. **Batch Processing**: Process multiple requests together when possible
5. **Context Pruning**: Limit message history to prevent token overflow

## Debugging Tips

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print agent transitions
def debug_run(agent, messages):
    client = Swarm()
    response = client.run(agent=agent, messages=messages, debug=True)
    print(f"Agent: {response.agent.name}")
    print(f"Messages: {len(response.messages)}")
    print(f"Context: {response.context_variables}")
    return response
```

Remember: Agents should be simple, focused, and composable. Build complex behavior through agent orchestration, not individual agent complexity!
