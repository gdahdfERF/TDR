"""
Represents the state of the simulation at any discrete time step (tick).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SimulationState:
    """Snapshot of the complete simulation state at tick t."""
    tick: int = 0
    is_terminated: bool = False
    winner: str = "NONE"  # 'ATTACKER', 'DEFENDER', 'DRAW', or 'NONE'
    compromised_nodes_count: int = 0
    total_nodes_count: int = 0
    attacker_objective_achieved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Stub: Convert state snapshot to serializable dictionary."""
        raise NotImplementedError("Serialization logic not implemented yet.")
