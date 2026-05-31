"""
Multi-Agent Orchestrator for IndoGovRAG

Coordinates the pipeline: QueryUnderstanding → Retrieval → LegalReasoning → ResponseSynthesis.
Each agent receives and returns a shared context dict.
"""

import asyncio
import time
import logging
from typing import Optional

from .query_understanding import QueryUnderstandingAgent
from .retrieval import RetrievalAgent
from .legal_reasoning import LegalReasoningAgent
from .response_synthesis import ResponseSynthesisAgent
from .base import BaseAgent
from .exceptions import OrchestratorError

logger = logging.getLogger(__name__)


class MultiAgentOrchestrator:
    """
    Central orchestrator for the IndoGovRAG multi-agent pipeline.

    Pipeline order:
        1. QueryUnderstandingAgent  (timeout=2s)  — extract entities
        2. RetrievalAgent           (timeout=5s)  — fetch chunks
        3. LegalReasoningAgent      (timeout=4s)  — analyze conflicts
        4. ResponseSynthesisAgent   (timeout=10s) — generate answer

    Usage:
        result = await MultiAgentOrchestrator().run("Apa syarat membuat KTP?")
    """

    def __init__(self, options: Optional[dict] = None):
        self.agents = {
            "query_understanding": QueryUnderstandingAgent(),
            "retrieval": RetrievalAgent(),
            "legal_reasoning": LegalReasoningAgent(),
            "response_synthesis": ResponseSynthesisAgent(),
        }

        # Pipeline order (name keys into self.agents)
        self.pipeline = [
            "query_understanding",
            "retrieval",
            "legal_reasoning",
            "response_synthesis",
        ]

        # Per-request options (top_k, etc.)
        self.options = options or {}

        logger.info(
            f"[Orchestrator] Initialized with pipeline: {' → '.join(self.pipeline)}"
        )

    async def run(self, query: str, options: Optional[dict] = None) -> dict:
        """
        Execute the full multi-agent pipeline.

        Args:
            query: Natural-language question in Indonesian or English.
            options: Optional per-request overrides (top_k, ...).

        Returns:
            dict with keys:
                answer        (str)   — final synthesized answer
                sources       (list)  — formatted source citations
                confidence    (float) — confidence score 0-1
                warnings      (list)  — legal/policy warnings
                agent_timings (dict) — elapsed seconds per agent
                metadata      (dict) — pipeline metadata
        """
        start_time = time.time()
        opts = {**self.options, **(options or {})}

        # Shared context dict passed through all agents
        context = {
            "query": query,
            "options": opts,
            "_agent_timings": {},
            "_errors": [],
        }

        logger.info(f"[Orchestrator] START query='{query[:80]}'")

        # Run each agent in sequence with timeout wrapping
        for agent_key in self.pipeline:
            agent: BaseAgent = self.agents[agent_key]

            agent_start = time.time()

            try:
                # run_with_timeout handles its own try/except and returns context
                context = await agent.run_with_timeout(context)

            except Exception as exc:
                # Unexpected error — log and continue (orchestrator handles gracefully)
                elapsed = time.time() - agent_start
                error_msg = f"Unexpected error in {agent_key}: {exc}"
                logger.error(f"[Orchestrator] {error_msg}")
                context.setdefault("_errors", []).append(error_msg)
                context[f"{agent_key}_error"] = exc

            # Record timing regardless of outcome
            elapsed = time.time() - agent_start
            context["_agent_timings"][agent_key] = round(elapsed, 3)

            # Log each agent's result
            timed_out = context.get(f"{agent_key}_timed_out", False)
            has_error = context.get(f"{agent_key}_error") is not None

            status = "TIMEOUT" if timed_out else ("ERROR" if has_error else "OK")
            logger.info(
                f"[Orchestrator]   {agent_key}: {status} "
                f"({elapsed:.3f}s, timed_out={timed_out})"
            )

            # If critical agents fail/timed-out, we still let the pipeline continue
            # so the user gets whatever partial results are available.

        total_elapsed = time.time() - start_time
        context["_total_elapsed"] = round(total_elapsed, 3)

        # Build final response dict
        response = self._build_response(context)
        logger.info(
            f"[Orchestrator] END   total={total_elapsed:.3f}s  "
            f"confidence={response.get('confidence', 0.0):.2f}"
        )

        return response

    def _build_response(self, context: dict) -> dict:
        """Extract and format the final response from agent outputs in context."""

        # Check for catastrophic failures (all agents failed)
        all_failed = all(
            context.get(f"{k}_error") or context.get(f"{k}_timed_out", False)
            for k in self.pipeline
        )

        if all_failed:
            raise OrchestratorError(
                message="All agents in the pipeline failed or timed out.",
                context={"query": context.get("query"), "errors": context.get("_errors", [])},
            )

        # Extract answer (from response_synthesis or fallback)
        final_answer = context.get("final_answer", "")
        if not final_answer:
            final_answer = (
                "Maaf, terjadi kesalahan dalam memproses pertanyaan Anda. "
                "Silakan coba lagi atau hubungi administrator."
            )

        # Extract confidence
        confidence = context.get("confidence", 0.0)
        if confidence == 0.0 and not context.get("chunks"):
            confidence = 0.0
        elif confidence == 0.0 and context.get("chunks"):
            # Estimate from chunk scores
            scores = [c.get("score", 0.0) for c in context.get("chunks", [])]
            if scores:
                confidence = round(sum(scores) / len(scores), 3)

        # Extract sources
        sources = context.get("sources", [])

        # Extract warnings
        warnings = context.get("warnings", [])
        # Add timeout warnings
        for agent_key in self.pipeline:
            if context.get(f"{agent_key}_timed_out"):
                warnings.append(f"Agent '{agent_key}' memerlukan waktu lebih lama dari biasanya.")
        # Add error warnings
        for agent_key in self.pipeline:
            err = context.get(f"{agent_key}_error")
            if err and not context.get(f"{agent_key}_timed_out"):
                warnings.append(f"Gagal memproses '{agent_key}': {err}")

        # Assembly metadata
        metadata = {
            "pipeline": self.pipeline,
            "agent_timings": context.get("_agent_timings", {}),
            "total_elapsed_s": context.get("_total_elapsed", 0.0),
            "retrieval_method": context.get("retrieval_method", "unknown"),
            "chunks_retrieved": len(context.get("chunks", [])),
            "response_generation_method": context.get("response_generation_method", "unknown"),
            "query_entities": context.get("query_entities", {}),
            "has_errors": bool(context.get("_errors")),
            "errors": context.get("_errors", []),
        }

        return {
            "answer": final_answer,
            "sources": sources,
            "confidence": confidence,
            "warnings": warnings[:10],  # cap at 10
            "metadata": metadata,
        }


# ── Sync convenience wrapper ────────────────────────────────────────────────────

def run_sync(query: str, options: Optional[dict] = None) -> dict:
    """
    Synchronous entry point for non-async callers (e.g. FastAPI sync endpoint).
    Runs the full async pipeline in a new event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        # Already in async context — schedule it
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                MultiAgentOrchestrator(options).run(query)
            )
            return future.result()
    except RuntimeError:
        # No running loop — safe to use asyncio.run
        return asyncio.run(MultiAgentOrchestrator(options).run(query))
