"""
Base agent class for all IndoGovRAG agents.
Provides async execution with timeout, logging, and error handling.
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

from .exceptions import AgentTimeoutError, AgentError

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all multi-agent components.

    Subclasses must implement `run()` which receives a shared context dict
    and returns an updated dict. Timeouts are enforced per agent.
    """

    name: str = "base_agent"
    timeout: float = 5.0  # seconds

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """
        Execute the agent's logic.

        Args:
            context: Shared context dict carrying data between agents.
                     Agents MUST read from it and write updated keys.

        Returns:
            Updated context dict (always, never None).
        """
        raise NotImplementedError

    async def run_with_timeout(self, context: dict) -> dict:
        """
        Execute `run()` with an asyncio timeout.

        Falls back to a minimal error payload on timeout so the pipeline
        can continue (orchestrator decides whether to halt or proceed).
        """
        start = time.time()
        logger.info(f"[{self.name}] START")

        try:
            async with asyncio.timeout(self.timeout):
                result = await self.run(context)

            elapsed = time.time() - start
            logger.info(f"[{self.name}] END  ({elapsed:.2f}s)")
            return result

        except asyncio.TimeoutError:
            elapsed = time.time() - start
            logger.warning(f"[{self.name}] TIMEOUT after {elapsed:.2f}s (limit={self.timeout}s)")
            # Return error payload in context so pipeline can continue
            context[f"{self.name}_error"] = AgentTimeoutError(self.name, self.timeout)
            context[f"{self.name}_timed_out"] = True
            return context

        except Exception as exc:
            elapsed = time.time() - start
            logger.error(f"[{self.name}] ERROR after {elapsed:.2f}s: {exc}")
            context[f"{self.name}_error"] = AgentError(self.name, str(exc), exc)
            return context

    def _get_timing(self, context: dict) -> Optional[float]:
        """Read agent timing from context if set by orchestrator."""
        return context.get("_agent_timings", {}).get(self.name)