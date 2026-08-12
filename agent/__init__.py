"""My AI Agent core package.

The runtime keeps the hot path lightweight: app -> AgentCore -> capability
router -> selected external capability/provider. Optional integrations are
loaded lazily by the components that need them.
"""

from agent.core import AgentCore, ExecutionResult, get_agent_core, run_agent

__all__ = [
    "AgentCore",
    "ExecutionResult",
    "get_agent_core",
    "run_agent",
]
