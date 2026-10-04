"""
Abstract base class defining the standard agent interface.
Enables plug-and-play replacement of rule-based logic with future LLM decision modules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    """
    Abstract interface for all cybersecurity simulation agents.
    Enforces the uniform lifecycle:
      1. observe(observation) -> Ingest visible telemetry
      2. select_action()      -> Return a validated action string
    """

    def __init__(self, agent_id: str, role: str, valid_actions: List[str]):
        self.agent_id: str = agent_id
        self.role: str = role  # 'ATTACKER' or 'DEFENDER'
        self.valid_actions: List[str] = list(valid_actions)
        self.last_observation: Dict[str, Any] = {}

    def observe(self, observation: Dict[str, Any]) -> None:
        """Ingest and record observation emitted by the environment."""
        self.last_observation = dict(observation)

    @abstractmethod
    def select_action(self) -> str:
        """
        Decide the next action to perform based on current observation.
        Must return an action string present in self.valid_actions.
        """
        pass

    def reset(self) -> None:
        """Reset internal memory/state for a new simulation run."""
        self.last_observation.clear()
