"""
Attacker Agent Module (V0.2).

Implements RuleBasedAttacker conforming to BaseAgent.
Supports strategic waiting ('low-and-slow' evasion vs. 'aggressive' rush).
Ready to be swapped with LLM_Attacker in V1.0.
"""

import random
from typing import Any, Dict, List, Optional
from ..base_agent import BaseAgent


class RuleBasedAttacker(BaseAgent):
    """
    Goal-oriented offensive agent that navigates the attack chain:
    Recon (scan) -> Access (login) -> Exfiltration (access_resource)
    Can strategically interleave 'wait' to cool down suspicion when turn budget permits.
    """

    VALID_ACTIONS: List[str] = ["scan", "login", "access_resource", "wait"]

    def __init__(
        self,
        agent_id: str = "attacker_ai",
        strategy: str = "adaptive",
        stealth_bias: float = 0.3,
        seed: Optional[int] = None,
    ):
        super().__init__(agent_id=agent_id, role="ATTACKER", valid_actions=self.VALID_ACTIONS)
        self.strategy = strategy  # "adaptive", "aggressive", "stealth"
        self.stealth_bias = stealth_bias
        self.rng = random.Random(seed)
        self.previous_action: Optional[str] = None

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset internal memory for a new episode."""
        super().reset()
        if seed is not None:
            self.rng = random.Random(seed)
        self.previous_action = None

    def select_action(self, obs: Optional[Dict[str, Any]] = None) -> str:
        """
        Choose the next offensive action.
        If obs is provided, updates observation buffer first.
        """
        if obs is not None:
            self.observe(obs)

        observation = self.last_observation

        # If already blocked or target reached, idle safely
        if observation.get("is_blocked") or observation.get("resource_accessed"):
            self.previous_action = "wait"
            return "wait"

        scanned = observation.get("scanned", False)
        authenticated = observation.get("authenticated", False)
        current_turn = observation.get("current_turn", 1)
        max_turns = observation.get("max_turns", 15)

        # Calculate minimum actions needed to achieve victory
        if not scanned:
            steps_needed = 3  # scan -> login -> access
        elif not authenticated:
            steps_needed = 2  # login -> access
        else:
            steps_needed = 1  # access

        turns_remaining = max(0, max_turns - current_turn + 1)

        # Strategic Waiting Logic:
        # If we have turn slack (turns_remaining > steps_needed), evaluate stealth.
        should_wait_stealth = False

        if self.strategy == "aggressive":
            # Aggressive: Never voluntarily wait; rush directly to objective
            should_wait_stealth = False

        elif self.strategy == "stealth":
            # Stealth: Always wait immediately after any loud action if turn slack exists
            if self.previous_action in ["scan", "login"] and turns_remaining > steps_needed:
                should_wait_stealth = True

        elif self.strategy == "adaptive":
            # Adaptive: If we just performed a loud action and have slack,
            # wait with probability proportional to stealth_bias to decay suspicion
            if self.previous_action in ["scan", "login"] and turns_remaining > steps_needed:
                if self.rng.random() < self.stealth_bias:
                    should_wait_stealth = True

        if should_wait_stealth:
            self.previous_action = "wait"
            return "wait"

        # Execute progressive attack steps
        if not scanned:
            action = "scan"
        elif not authenticated:
            action = "login"
        else:
            action = "access_resource"

        self.previous_action = action
        return action


# Alias for backwards compatibility
AttackerAgent = RuleBasedAttacker
