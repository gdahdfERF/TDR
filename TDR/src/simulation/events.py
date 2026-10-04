"""
Defines discrete events occurring within the simulation.
Every interaction between agents and the simulated network produces an event.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
import time


class EventType(str, Enum):
    """Types of events generated inside the simulation."""
    SIMULATION_START = "SIMULATION_START"
    SIMULATION_END = "SIMULATION_END"
    TICK_ADVANCED = "TICK_ADVANCED"
    
    # Attacker Events
    ATTACK_ATTEMPTED = "ATTACK_ATTEMPTED"
    ATTACK_SUCCEEDED = "ATTACK_SUCCEEDED"
    ATTACK_FAILED = "ATTACK_FAILED"
    NODE_COMPROMISED = "NODE_COMPROMISED"
    DATA_EXFILTRATED = "DATA_EXFILTRATED"
    
    # Defender Events
    TELEMETRY_INSPECTED = "TELEMETRY_INSPECTED"
    THREAT_DETECTED = "THREAT_DETECTED"
    FALSE_ALARM = "FALSE_ALARM"
    NODE_ISOLATED = "NODE_ISOLATED"
    VULNERABILITY_PATCHED = "VULNERABILITY_PATCHED"
    IP_BLOCKED = "IP_BLOCKED"


@dataclass
class SimulationEvent:
    """Standardized event record generated during simulation ticks."""
    event_id: str
    event_type: EventType
    tick: int
    actor: str  # 'ATTACKER', 'DEFENDER', 'SYSTEM'
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event object to dictionary for logging and serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "tick": self.tick,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "details": self.details
        }
