"""
Telemetry Logger Module (V1.0).

Structured JSON-Lines event logger for simulation runs.
Captures turn-by-turn state, suspicion, evidence, model metadata, and outcomes
for experimental evaluation.

Windows-safe: all console output uses ASCII-only characters to avoid cp1252
UnicodeEncodeError on default Windows terminals.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class SimpleLogger:
    """Logs simulation events in JSON-Lines format and pretty-prints to console."""

    def __init__(self, log_file: str = "data/logs/simulation.jsonl", verbose: bool = True):
        self.log_path = Path(log_file)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.events: List[Dict[str, Any]] = []

    def clear(self) -> None:
        """Clear previous run logs from file."""
        self.events.clear()
        self.log_path.write_text("", encoding="utf-8")

    @staticmethod
    def _safe_print(text: str) -> None:
        """
        Print text safely on any platform, including Windows consoles that use
        legacy code pages (e.g. cp1252) which cannot encode Unicode box-drawing chars.
        Falls back to writing raw UTF-8 bytes if the default encoding fails.
        """
        try:
            print(text)
        except UnicodeEncodeError:
            sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))

    def log(
        self,
        turn: int,
        actor: str,
        action: str,
        result: str,
        suspicion_level: float = 0.0,
        evidence_score: float = 0.0,
        detection_status: str = "Undetected",
        blocked_status: bool = False,
        resource_access_status: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an action and the current observable metrics."""
        entry = {
            "turn": turn,
            "actor": actor,
            "action": action,
            "result": result,
            "suspicion_level": round(suspicion_level, 3),
            "evidence_score": round(evidence_score, 3),
            "detection_status": detection_status,
            "blocked_status": blocked_status,
            "resource_access_status": resource_access_status,
            "details": details or {},
        }
        self.events.append(entry)

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        if self.verbose:
            state_summary = f"[Susp:{suspicion_level:.2f} | Evid:{evidence_score:.2f}]"
            self._safe_print(
                f"[Turn {turn:02d}] [{actor:8s}] Action: {action:<16s} "
                f"{state_summary:<20s} | {result}"
            )
            if details and details.get("reasoning"):
                model_tag = (
                    f" ({details['model_name']})" if details.get("model_name") else ""
                )
                # ASCII prefix avoids UnicodeEncodeError on cp1252 Windows consoles
                self._safe_print(
                    f"           -> Reasoning{model_tag}: {details['reasoning']}"
                )
