"""
Defines the action space available to the simulated defender / blue team agent.
Actions correspond to typical SOC (Security Operations Center) remediation and response workflows.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class DefenderActionType(str, Enum):
    """Supported simulated defender actions."""
    ANALYZE_TELEMETRY = "ANALYZE_TELEMETRY"   # Inspect recent node/network audit logs
    ISOLATE_NODE = "ISOLATE_NODE"             # Quarantine suspect machine from network
    PATCH_VULNERABILITY = "PATCH_VULNERABILITY"# Deploy simulated security update
    BLOCK_IP = "BLOCK_IP"                     # Add firewall rule to block suspicious source IP
    RESET_CREDENTIALS = "RESET_CREDENTIALS"   # Revoke and reset compromised account credentials
    NO_OP = "NO_OP"                           # Do nothing (monitor passively)


@dataclass
class DefenderAction:
    """Represents an instantiated defender remediation or monitoring action."""
    action_type: DefenderActionType
    target_node_id: Optional[str] = None
    target_ip: Optional[str] = None
    target_cve_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
