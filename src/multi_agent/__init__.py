"""
Multi-Agent Orchestrator for IndoGovRAG

Agents:
- QueryUnderstandingAgent: analyzes intent, extracts entities
- RetrievalAgent: queries ChromaDB with hybrid search
- LegalReasoningAgent: analyzes conflicts, revisions, groupings
- ResponseSynthesisAgent: generates Indonesian-language answer

Usage:
    from src.multi_agent import MultiAgentOrchestrator
    result = await MultiAgentOrchestrator().run("Apa syarat membuat KTP?")
"""

from .orchestrator import MultiAgentOrchestrator
from .base import BaseAgent
from .exceptions import AgentTimeoutError, AgentError, OrchestratorError

__all__ = [
    "MultiAgentOrchestrator",
    "BaseAgent",
    "AgentTimeoutError",
    "AgentError",
    "OrchestratorError",
]
