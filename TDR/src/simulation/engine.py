"""
Simulation Engine Module (V0.2).

Orchestrates turn-by-turn discrete execution between Attacker AI, Defender AI,
and the simulated environment with full seed reproducibility.
"""

from typing import Any, Dict, Optional
from ..environment.simple_env import SimpleEnvironment
from ..agents.base_agent import BaseAgent
from ..telemetry.logger import SimpleLogger


class SimulationEngine:
    """
    Coordinates turn loop, enforces rules, collects telemetry,
    and computes final outcome metrics.
    """

    def __init__(
        self,
        env: SimpleEnvironment,
        attacker: BaseAgent,
        defender: BaseAgent,
        logger: Optional[SimpleLogger] = None,
        max_turns: int = 15,
        seed: Optional[int] = None,
    ):
        self.env = env
        self.attacker = attacker
        self.defender = defender
        self.logger = logger
        self.max_turns = max_turns
        self.seed = seed

    def _get_attacker_details(self, success: bool) -> Dict[str, Any]:
        """Extract logging metadata from attacker agent (including model and reasoning)."""
        details: Dict[str, Any] = {"success": success}
        if hasattr(self.attacker, "model_name") and self.attacker.model_name:
            details["model_name"] = self.attacker.model_name
        if hasattr(self.attacker, "last_reasoning") and self.attacker.last_reasoning:
            details["reasoning"] = self.attacker.last_reasoning
        return details

    def run(self) -> Dict[str, Any]:
        """
        Execute simulation until win condition or max_turns reached.
        Returns detailed performance metrics.
        """
        self.env.reset(seed=self.seed)
        if hasattr(self.attacker, "reset"):
            self.attacker.reset(seed=self.seed)
        if hasattr(self.defender, "reset"):
            self.defender.reset()

        if self.logger:
            self.logger.clear()

        winner = "Defender"
        turns_executed = 0

        for turn in range(1, self.max_turns + 1):
            turns_executed = turn

            # ----------------------------------------------------
            # Turn Initialization: Benign traffic & background noise
            # ----------------------------------------------------
            self.env.start_turn(turn)

            # Both agents observe environment state at start of turn
            attacker_obs = self.env.get_attacker_obs()
            self.attacker.observe(attacker_obs)
            attacker_action = self.attacker.select_action()

            defender_obs = self.env.get_defender_obs()
            self.defender.observe(defender_obs)
            defender_action = self.defender.select_action()

            # ----------------------------------------------------
            # Resolution: Containment vs. Progression
            # ----------------------------------------------------
            if defender_action == "block":
                # Defender attempts active containment
                def_success, def_msg = self.env.execute_defender_action("block")

                if self.logger:
                    self.logger.log(
                        turn=turn,
                        actor="Defender",
                        action="block",
                        result=def_msg,
                        suspicion_level=self.env.suspicion_level,
                        evidence_score=self.env.evidence_score,
                        detection_status="Detected" if self.env.detected else "Undetected",
                        blocked_status=self.env.is_blocked,
                        resource_access_status=self.env.resource_accessed,
                        details={"success": def_success, "false_positive": self.env.false_positive},
                    )

                if def_success:
                    # Valid containment verified: Intruder quarantined before action completes
                    winner = "Defender"
                    break

                # False positive: Block failed / disrupted legitimate services; intruder remains active
                att_success, att_msg = self.env.execute_attacker_action(attacker_action)
                if self.logger:
                    self.logger.log(
                        turn=turn,
                        actor="Attacker",
                        action=attacker_action,
                        result=att_msg,
                        suspicion_level=self.env.suspicion_level,
                        evidence_score=self.env.evidence_score,
                        detection_status="Detected" if self.env.detected else "Undetected",
                        blocked_status=self.env.is_blocked,
                        resource_access_status=self.env.resource_accessed,
                        details=self._get_attacker_details(att_success),
                    )
                if self.env.resource_accessed:
                    winner = "Attacker"
                    break

            else:
                # Defender is passively monitoring or actively investigating
                att_success, att_msg = self.env.execute_attacker_action(attacker_action)
                if self.logger:
                    self.logger.log(
                        turn=turn,
                        actor="Attacker",
                        action=attacker_action,
                        result=att_msg,
                        suspicion_level=self.env.suspicion_level,
                        evidence_score=self.env.evidence_score,
                        detection_status="Detected" if self.env.detected else "Undetected",
                        blocked_status=self.env.is_blocked,
                        resource_access_status=self.env.resource_accessed,
                        details=self._get_attacker_details(att_success),
                    )

                if self.env.resource_accessed:
                    winner = "Attacker"
                    break

                def_success, def_msg = self.env.execute_defender_action(defender_action)
                if self.logger:
                    self.logger.log(
                        turn=turn,
                        actor="Defender",
                        action=defender_action,
                        result=def_msg,
                        suspicion_level=self.env.suspicion_level,
                        evidence_score=self.env.evidence_score,
                        detection_status="Detected" if self.env.detected else "Undetected",
                        blocked_status=self.env.is_blocked,
                        resource_access_status=self.env.resource_accessed,
                        details={"success": def_success},
                    )

        else:
            # Max turns exhausted without breach or containment
            if self.env.resource_accessed:
                winner = "Attacker"
            elif self.env.false_positive:
                winner = "Draw"
            else:
                winner = "Defender"

        return {
            "winner": winner,
            "attack_success": self.env.resource_accessed,
            "detected": self.env.detected,
            "false_positive": self.env.false_positive,
            "total_turns": turns_executed,
            "detection_turn": self.env.detection_turn,
            "containment_turn": self.env.containment_turn,
            "final_suspicion": round(self.env.suspicion_level, 3),
            "final_evidence": round(self.env.evidence_score, 3),
        }
