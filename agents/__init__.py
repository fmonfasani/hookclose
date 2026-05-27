"""
agents/ — Specialized agent descriptors and registry.

Per the design brief, **no agent logic is implemented yet**. This package
declares the shape an agent must take, the capabilities it can advertise,
and the registry surface the runtime uses to look them up.

Every agent will eventually implement `contracts.AgentPort`.
"""

from agents.base import AgentBase
from agents.capabilities import Capability, CapabilityName, CapabilitySpec
from agents.descriptor import AgentDescriptor
from agents.registry import AgentRegistry

__all__ = [
    "AgentBase",
    "AgentDescriptor",
    "AgentRegistry",
    "Capability",
    "CapabilityName",
    "CapabilitySpec",
]
