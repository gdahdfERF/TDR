"""
Defines simulated software services, ports, and associated vulnerabilities.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Vulnerability:
    """Represents a simulated vulnerability in a service (e.g. CVE-XXXX)."""
    cve_id: str
    severity: str  # e.g., 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    exploit_complexity: str  # e.g., 'LOW', 'MEDIUM', 'HIGH'
    is_patched: bool = False


@dataclass
class Service:
    """Represents a simulated network service listening on a port."""
    name: str
    port: int
    is_running: bool = True
    vulnerabilities: List[Vulnerability] = field(default_factory=list)

    def patch_vulnerability(self, cve_id: str) -> bool:
        """Stub: Patch a specific vulnerability on this service."""
        raise NotImplementedError("Logic to patch vulnerability not implemented yet.")

    def add_vulnerability(self, vulnerability: Vulnerability) -> None:
        """Stub: Add a vulnerability to this service."""
        raise NotImplementedError("Logic to add vulnerability not implemented yet.")
