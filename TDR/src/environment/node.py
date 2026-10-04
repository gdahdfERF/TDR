"""
Defines a simulated host (workstation, server, router) inside the network.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .service import Service


@dataclass
class Node:
    """Represents an individual computer/device within the simulated network."""
    node_id: str
    ip_address: str
    subnet_id: str
    os_type: str  # e.g., 'Linux', 'Windows'
    role: str     # e.g., 'web_server', 'database', 'workstation'
    is_compromised: bool = False
    is_isolated: bool = False
    has_target_data: bool = False
    services: Dict[int, Service] = field(default_factory=dict)
    compromise_level: str = "NONE"  # e.g., 'NONE', 'USER', 'ROOT'

    def isolate(self) -> None:
        """Stub: Disconnect this node from communicating with the rest of the network."""
        raise NotImplementedError("Logic to isolate node not implemented yet.")

    def reconnect(self) -> None:
        """Stub: Re-enable network access for this node."""
        raise NotImplementedError("Logic to reconnect node not implemented yet.")

    def get_open_ports(self) -> List[int]:
        """Stub: Return list of currently open ports on this node."""
        raise NotImplementedError("Logic to query open ports not implemented yet.")
