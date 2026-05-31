"""
Custom exceptions for the multi-agent system.
"""


class AgentTimeoutError(Exception):
    """Raised when an agent exceeds its configured timeout."""

    def __init__(self, agent_name: str, timeout: float, message: str = ""):
        self.agent_name = agent_name
        self.timeout = timeout
        default = f"Agent '{agent_name}' timed out after {timeout}s"
        super().__init__(message or default)


class AgentError(Exception):
    """Raised when an agent encounters a runtime error."""

    def __init__(self, agent_name: str, message: str, cause: Exception = None):
        self.agent_name = agent_name
        self.cause = cause
        full = f"Agent '{agent_name}' failed: {message}"
        if cause:
            full += f" (caused by: {type(cause).__name__}: {cause})"
        super().__init__(full)


class OrchestratorError(Exception):
    """Raised when the orchestrator pipeline encounters an unrecoverable error."""

    def __init__(self, message: str, failed_agent: str = None, context: dict = None):
        self.failed_agent = failed_agent
        self.context = context or {}
        super().__init__(message)
