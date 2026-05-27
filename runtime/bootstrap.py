"""Boot orchestrator — wires the component graph at startup.

Intentionally a scaffold. Concrete bindings (LLM provider, VCS adapter, event
bus implementation, …) are intentionally NOT wired here yet, per the design
brief (contracts first, no business logic).
"""

from __future__ import annotations

from runtime.config import RuntimeSettings
from runtime.lifecycle import Lifecycle
from runtime.registry import ComponentRegistry


async def build_registry(settings: RuntimeSettings) -> ComponentRegistry:
    """Construct the component registry for the current process.

    Bindings happen here, in this exact order:
      1. Telemetry (so everything else can emit traces)
      2. OperationalMemory (Redis-backed)
      3. EventBus
      4. EpisodicMemory + SemanticMemory
      5. TaskRunner (Celery)
      6. WorkflowEngine
      7. Adapters: LLM providers, VCS, Sandbox, CodeExecutor
      8. Agent registry

    Each step is intentionally left as a stub. Adapters will be wired in
    follow-up commits.
    """
    del settings  # unused until adapters are wired
    return ComponentRegistry()


def build_lifecycle() -> Lifecycle:
    """Declare the lifecycle stages. Empty stages here intentionally."""
    return Lifecycle()
