"""Build-orchestration loop — blueprint entrypoint.

This is the high-level control loop that drives the autonomous build process. It
is intentionally **not yet wired** to the runtime: the concrete steps below are
implemented across later phases (providers, routing, workers, chaining,
self-healing). Until then this module is import-safe and does nothing on import.

Intended deterministic loop::

    state = load_state()                  # runtime/state.py — RuntimeStateStore
    while not state.done:
        prompt = get_next_prompt(state)   # next pending prompt for the phase
        result = dispatch(prompt)         # route -> provider/worker (Prompt 20/21/22/23)
        state = record(state, result)     # mark completed/failed, persist
        if result.failed:
            create_repair_task(result)    # self-healing (Prompt 25), bounded

The loop is bounded and auditable: every iteration persists runtime state and
emits events; no step runs between deterministic transitions.
"""

from __future__ import annotations


def main() -> None:
    raise NotImplementedError(
        "The orchestration loop is wired up in the autonomy phase (Prompts 24-25). See ROADMAP.md."
    )


if __name__ == "__main__":
    main()
