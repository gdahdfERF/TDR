"""
Defender Agent Module (V0.2).

Implements RuleBasedDefender conforming to BaseAgent.
Makes decisions strictly from telemetry observations (no hidden ground-truth omniscience).
Ready to be swapped with LLM_Defender in V1.0.
"""

from typing import Any, Dict, List, Optional
from ..base_agent import BaseAgent


class RuleBasedDefender(BaseAgent):
    """
    Blue-team defensive agent modeling a Security Operations Center (SOC) analyst.
    Monitors telemetry, triggers forensic investigations when anomalies occur,
    and isolates hosts when sufficient evidence is verified.
    """

    VALID_ACTIONS: List[str] = ["monitor", "investigate", "block"]

    def __init__(
        self,
        agent_id: str = "defender_ai",
        policy: str = "balanced",
        investigate_threshold: float = 0.25,
        risk_threshold: float = 0.70,
    ):
        super().__init__(agent_id=agent_id, role="DEFENDER", valid_actions=self.VALID_ACTIONS)
        self.policy = policy  # "balanced", "cautious", "aggressive"
        self.investigate_threshold = investigate_threshold
        self.risk_threshold = risk_threshold

    def select_action(self, obs: Optional[Dict[str, Any]] = None) -> str:
        """
        Choose next defensive action based strictly on telemetry observation.
        Does not access hidden environment state.
        """
        if obs is not None:
            self.observe(obs)

        observation = self.last_observation

        # If containment already executed, continue routine monitoring
        if observation.get("is_blocked", False):
            return "monitor"

        is_detected = observation.get("is_detected", False)
        evidence_score = observation.get("evidence_score", 0.0)
        suspicion = observation.get("observed_suspicion", 0.0)
        logs = observation.get("recent_logs", [])

        # Check for alert indicators in logs
        has_suspicious_logs = any(
            any(tag in log for tag in ["ALERT:", "WARNING:", "CRITICAL:"])
            for log in logs
        )

        # Policy 1: Aggressive / Trigger-happy
        if self.policy == "aggressive":
            # If high suspicion but evidence not fully verified, aggressive defender might panic-block
            if is_detected or evidence_score >= self.risk_threshold or suspicion >= 0.60:
                return "block"
            if suspicion >= self.investigate_threshold or has_suspicious_logs:
                return "investigate"
            return "monitor"

        # Policy 2: Cautious
        elif self.policy == "cautious":
            # Only blocks with strictly confirmed detection (evidence >= threshold)
            if is_detected or evidence_score >= self.risk_threshold:
                return "block"
            if suspicion >= 0.40:
                return "investigate"
            return "monitor"

        # Policy 3: Balanced (default)
        else:
            # Block when threat is verified by forensic evidence
            if is_detected or evidence_score >= self.risk_threshold:
                return "block"

            # Investigate when suspicion rises above threshold or anomalous logs appear
            if suspicion >= self.investigate_threshold or has_suspicious_logs:
                return "investigate"

            # Baseline passive monitoring
            return "monitor"


# Alias for backwards compatibility
DefenderAgent = RuleBasedDefender
