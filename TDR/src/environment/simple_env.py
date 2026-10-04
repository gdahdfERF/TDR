"""
Simulated Cybersecurity Environment (V0.2).

Models a target host with:
- A protected resource
- An authentication service
- Controlled benign background traffic noise
- Transparent suspicion level and evidence accumulation models
- Valid containment vs. false positive handling
"""

import random
from typing import Any, Dict, List, Optional, Tuple


class SimpleEnvironment:
    """
    Pure software simulation of an enterprise host and its security telemetry.
    All operations are kept in-memory with reproducible random seed support.
    """

    DETECTION_THRESHOLD: float = 0.70
    SCAN_SUSPICION_DELTA: float = 0.30
    LOGIN_SUSPICION_DELTA: float = 0.35
    ACCESS_SUSPICION_DELTA: float = 0.40
    WAIT_DECAY_DELTA: float = 0.15

    BENIGN_MESSAGES: List[str] = [
        "Routine employee workstation heartbeat received.",
        "Automated backup synchronizing user directory.",
        "Internal DNS resolution request processed.",
        "Standard HTTPS telemetry poll from client endpoint.",
        "Scheduled virus definition update completed.",
    ]

    def __init__(self, seed: Optional[int] = None, max_turns: int = 15):
        self.seed = seed
        self.max_turns = max_turns
        self.rng = random.Random(seed)
        self.reset()

    def reset(self, seed: Optional[int] = None) -> None:
        """Reset environment to a clean baseline state."""
        if seed is not None:
            self.seed = seed
            self.rng = random.Random(seed)

        # Ground-truth attacker progression
        self.scanned: bool = False
        self.authenticated: bool = False
        self.resource_accessed: bool = False
        self.is_blocked: bool = False

        # Metrics and tracking
        self.current_turn: int = 0
        self.detected: bool = False
        self.detection_turn: Optional[int] = None
        self.containment_turn: Optional[int] = None
        self.false_positive: bool = False
        self.false_positive_count: int = 0

        # Signals
        self.suspicion_level: float = 0.0  # Range: [0.0, 1.0]
        self.evidence_score: float = 0.0   # Range: [0.0, 1.0]
        self.recent_logs: List[str] = []

    def start_turn(self, turn: int) -> None:
        """
        Advance turn and generate controlled benign background activity.
        Every turn, normal operations add slight telemetry variance.
        """
        self.current_turn = turn
        self.recent_logs.clear()

        # Benign background noise (+0.02 to +0.08)
        benign_noise = self.rng.uniform(0.02, 0.08)
        self.suspicion_level = min(1.0, self.suspicion_level + benign_noise)

        # Inject a realistic routine log message
        routine_msg = self.rng.choice(self.BENIGN_MESSAGES)
        self.recent_logs.append(f"BENIGN: {routine_msg}")

    def execute_attacker_action(self, action: str) -> Tuple[bool, str]:
        """
        Execute an action chosen by the attacker.
        Updates progression and suspicion according to transparent rules.
        """
        if self.is_blocked:
            return False, "BLOCKED: Firewall denies all incoming packets from intruder IP."

        if action == "scan":
            self.scanned = True
            self.suspicion_level = min(1.0, self.suspicion_level + self.SCAN_SUSPICION_DELTA)
            self.recent_logs.append("ALERT: Port scan signature detected on authentication port.")
            return True, "Port scan complete: Authentication service identified."

        elif action == "login":
            if not self.scanned:
                return False, "Failed: Target port unknown. Must execute 'scan' first."
            self.authenticated = True
            self.suspicion_level = min(1.0, self.suspicion_level + self.LOGIN_SUSPICION_DELTA)
            self.recent_logs.append("WARNING: Suspicious credential authentication from unknown source.")
            return True, "Login successful: User shell access obtained."

        elif action == "access_resource":
            if not self.authenticated:
                return False, "Failed: Access denied. Must authenticate with 'login' first."
            self.resource_accessed = True
            # access_resource adds +0.40 suspicion (not an automatic 1.0)
            self.suspicion_level = min(1.0, self.suspicion_level + self.ACCESS_SUSPICION_DELTA)
            self.recent_logs.append("CRITICAL: Unauthorized read of protected research database.")
            return True, "Objective achieved: Protected resource exfiltrated!"

        elif action == "wait":
            # Strategic stealth pause: natural decay cools down suspicion
            self.suspicion_level = max(0.0, self.suspicion_level - self.WAIT_DECAY_DELTA)
            self.recent_logs.append("INFO: Low activity period recorded on host.")
            return True, f"Idling in stealth: Suspicion decayed by {self.WAIT_DECAY_DELTA:.2f}."

        return False, f"Unknown attacker action '{action}'."

    def execute_defender_action(self, action: str) -> Tuple[bool, str]:
        """
        Execute an action chosen by the defender.
        Handles investigation, evidence accumulation, and valid vs. false positive blocking.
        """
        if action == "monitor":
            # Passive dashboard observation: safe, but accumulates zero evidence
            return True, "Passive monitoring: Logs reviewed; no active investigation initiated."

        elif action == "investigate":
            # Active forensics: accumulates evidence proportional to current suspicion
            evidence_gain = self.suspicion_level * 0.60
            self.evidence_score = min(1.0, self.evidence_score + evidence_gain)

            # Check if accumulated evidence crosses the detection threshold
            if self.evidence_score >= self.DETECTION_THRESHOLD and not self.detected:
                self.detected = True
                self.detection_turn = self.current_turn
                self.recent_logs.append("FORENSICS: Threat confirmed! Malicious IP and signature verified.")
                return True, (
                    f"Investigation conclusive (+{evidence_gain:.2f}): Evidence reached "
                    f"{self.evidence_score:.2f} >= {self.DETECTION_THRESHOLD:.2f} (THREAT CONFIRMED)."
                )

            return True, (
                f"Investigation complete (+{evidence_gain:.2f}): Evidence accumulated to "
                f"{self.evidence_score:.2f}/{self.DETECTION_THRESHOLD:.2f}."
            )

        elif action == "block":
            # Remediation: Must have sufficient evidence (>= 0.70) for valid containment
            if self.evidence_score >= self.DETECTION_THRESHOLD:
                self.is_blocked = True
                self.containment_turn = self.current_turn
                self.recent_logs.append("CONTAINMENT: Intruder IP isolated with verified forensic evidence.")
                return True, (
                    f"VALID CONTAINMENT: Intruder blocked with verified evidence "
                    f"({self.evidence_score:.2f} >= {self.DETECTION_THRESHOLD:.2f})."
                )
            else:
                # False Positive: Premature containment without evidence
                self.false_positive = True
                self.false_positive_count += 1
                self.recent_logs.append(
                    f"FALSE POSITIVE: Premature block executed (Evidence {self.evidence_score:.2f} < "
                    f"{self.DETECTION_THRESHOLD:.2f}). Normal operations disrupted!"
                )
                return False, (
                    f"FALSE POSITIVE: Block aborted/disrupted legitimate users! Evidence "
                    f"({self.evidence_score:.2f}) was below required threshold ({self.DETECTION_THRESHOLD:.2f}). "
                    f"Intruder remains unblocked."
                )

        return False, f"Unknown defender action '{action}'."

    def get_attacker_obs(self) -> Dict[str, Any]:
        """
        Attacker observation space:
        Only contains progress on target system and turn budget.
        """
        return {
            "scanned": self.scanned,
            "authenticated": self.authenticated,
            "resource_accessed": self.resource_accessed,
            "is_blocked": self.is_blocked,
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
        }

    def get_defender_obs(self) -> Dict[str, Any]:
        """
        Defender observation space:
        Only contains telemetry, evidence, logs, and detection status.
        Does NOT expose hidden attacker internal flags.
        """
        return {
            "observed_suspicion": round(self.suspicion_level, 3),
            "evidence_score": round(self.evidence_score, 3),
            "is_detected": self.detected,
            "is_blocked": self.is_blocked,
            "recent_logs": list(self.recent_logs),
            "current_turn": self.current_turn,
            "max_turns": self.max_turns,
        }
