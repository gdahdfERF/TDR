"""
Metrics and Evaluation Module (V0.2).

Aggregates individual simulation runs and computes quantitative research metrics:
- Win rates (Attacker, Defender, Draw)
- Detection and False Positive rates
- Mean Time to Detect (MTTD) and Contain (MTTC)
- Turn distributions
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class MetricsCollector:
    """Collects individual run metrics and computes statistical summaries."""

    def __init__(self, output_dir: str = "data/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runs: List[Dict[str, Any]] = []

    def record_run(self, run_id: int, result: Dict[str, Any]) -> None:
        """Record a completed simulation run."""
        record = {"run_id": run_id, **result}
        self.runs.append(record)

    def compute_summary(self) -> Dict[str, Any]:
        """Compute aggregated statistical metrics across all recorded runs."""
        total = len(self.runs)
        if total == 0:
            return {}

        attacker_wins = sum(1 for r in self.runs if r["winner"] == "Attacker")
        defender_wins = sum(1 for r in self.runs if r["winner"] == "Defender")
        draws = sum(1 for r in self.runs if r["winner"] == "Draw")
        detected_count = sum(1 for r in self.runs if r.get("detected", False))
        fp_count = sum(1 for r in self.runs if r.get("false_positive", False))

        detection_turns = [r["detection_turn"] for r in self.runs if r.get("detection_turn") is not None]
        containment_turns = [r["containment_turn"] for r in self.runs if r.get("containment_turn") is not None]
        all_turns = [r["total_turns"] for r in self.runs]

        avg_detection_turn = (sum(detection_turns) / len(detection_turns)) if detection_turns else None
        avg_containment_turn = (sum(containment_turns) / len(containment_turns)) if containment_turns else None
        avg_turns = sum(all_turns) / total if all_turns else 0.0

        return {
            "total_runs": total,
            "attacker_wins": attacker_wins,
            "defender_wins": defender_wins,
            "draws": draws,
            "attacker_win_rate": (attacker_wins / total) * 100.0,
            "defender_win_rate": (defender_wins / total) * 100.0,
            "draw_rate": (draws / total) * 100.0,
            "detection_rate": (detected_count / total) * 100.0,
            "false_positive_rate": (fp_count / total) * 100.0,
            "avg_detection_turn": avg_detection_turn,
            "avg_containment_turn": avg_containment_turn,
            "avg_turns": round(avg_turns, 2),
        }

    def export_to_csv(self, filename: str = "benchmark_metrics.csv") -> Path:
        """Export raw run records to CSV format for data analysis."""
        out_path = self.output_dir / filename
        if not self.runs:
            return out_path

        fieldnames = list(self.runs[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.runs)
        return out_path
