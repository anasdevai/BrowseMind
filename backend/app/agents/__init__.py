"""
Agent orchestration system for natural language browser control.
Provides base agent class and specialized agents for command processing.
"""
from app.agents.base_agent import BaseAgent
from app.agents.main_agent import MainAgent

__all__ = ["BaseAgent", "MainAgent"]
