"""
Defines the action space available to the simulated attacker agent.
Actions mimic MITRE ATT&CK tactics without using any real exploit payloads.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class AttackerActionType(str, Enum):
    """Supported simulated attacker actions."""
    RECON_SCAN = "RECON_SCAN"                 # Port scan / discovery
    EXPLOIT_SERVICE = "EXPLOIT_SERVICE"       # Exploit known service vulnerability
    BRUTE_FORCE = "BRUTE_FORCE"               # Password guess / brute-force
    PRIVILEGE_ESCALATE = "PRIVILEGE_ESCALATE" # Elevate permissions on compromised node
    LATERAL_MOVE = "LATERAL_MOVE"             # Move to adjacent reachable node
    EXFILTRATE_DATA = "EXFILTRATE_DATA"       # Extract sensitive target data
    WAIT = "WAIT"                             # Idle / stealth pause


@dataclass
class AttackerAction:
    """Represents an instantiated attacker action with target parameters."""
    action_type: AttackerActionType
    target_node_id: Optional[str] = None
    target_port: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
