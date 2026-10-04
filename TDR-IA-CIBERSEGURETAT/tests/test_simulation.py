"""
Integration Tests for Simulation Engine and Multi-Run Evaluation (V0.2).
Verifies end-to-end runs, winner conditions, seed reproducibility, and metrics collection.
"""

import unittest
from src.environment.simple_env import SimpleEnvironment
from src.agents.attacker.attacker_agent import RuleBasedAttacker
from src.agents.defender.defender_agent import RuleBasedDefender
from src.simulation.engine import SimulationEngine
from src.telemetry.metrics import MetricsCollector


class TestSimulation(unittest.TestCase):
    def test_attacker_victory_run(self):
        """Verify simulation where attacker successfully accesses resource."""
        env = SimpleEnvironment(seed=42, max_turns=10)
        # Aggressive attacker rushes; cautious defender waits for high threshold
        attacker = RuleBasedAttacker(strategy="aggressive", seed=42)
        defender = RuleBasedDefender(policy="cautious")

        engine = SimulationEngine(env=env, attacker=attacker, defender=defender, max_turns=10, seed=42)
        result = engine.run()

        self.assertEqual(result["winner"], "Attacker")
        self.assertTrue(result["attack_success"])

    def test_defender_containment_run(self):
        """Verify simulation where defender successfully detects and contains threat."""
        env = SimpleEnvironment(seed=100, max_turns=15)
        # Stealth attacker gives defender multiple turns to investigate and accumulate evidence
        attacker = RuleBasedAttacker(strategy="stealth", stealth_bias=1.0, seed=100)
        defender = RuleBasedDefender(policy="balanced")

        engine = SimulationEngine(env=env, attacker=attacker, defender=defender, max_turns=15, seed=100)
        result = engine.run()

        self.assertEqual(result["winner"], "Defender")
        self.assertTrue(result["detected"])
        self.assertIsNotNone(result["containment_turn"])

    def test_seed_reproducibility(self):
        """Verify that running the simulation with the exact same seed produces identical results."""
        def run_sim(seed):
            env = SimpleEnvironment(seed=seed, max_turns=10)
            att = RuleBasedAttacker(strategy="adaptive", seed=seed)
            df = RuleBasedDefender(policy="balanced")
            eng = SimulationEngine(env=env, attacker=att, defender=df, max_turns=10, seed=seed)
            return eng.run()

        res1 = run_sim(seed=12345)
        res2 = run_sim(seed=12345)

        self.assertEqual(res1, res2)

    def test_seed_variation(self):
        """Verify that different seeds produce different outcomes or turn counts across episodes."""
        results = set()
        for s in [1, 2, 3, 4, 5, 6, 7, 8]:
            env = SimpleEnvironment(seed=s, max_turns=10)
            att = RuleBasedAttacker(strategy="adaptive", seed=s)
            df = RuleBasedDefender(policy="balanced")
            eng = SimulationEngine(env=env, attacker=att, defender=df, max_turns=10, seed=s)
            r = eng.run()
            results.add((r["winner"], r["total_turns"]))

        # Must observe at least 2 distinct trajectory outcomes
        self.assertGreater(len(results), 1)

    def test_multiple_runs_metrics_collector(self):
        """Verify MetricsCollector aggregates multi-run statistics correctly."""
        collector = MetricsCollector()
        collector.record_run(1, {
            "winner": "Attacker",
            "attack_success": True,
            "detected": False,
            "false_positive": False,
            "total_turns": 3,
            "detection_turn": None,
            "containment_turn": None,
        })
        collector.record_run(2, {
            "winner": "Defender",
            "attack_success": False,
            "detected": True,
            "false_positive": False,
            "total_turns": 5,
            "detection_turn": 3,
            "containment_turn": 5,
        })

        summary = collector.compute_summary()
        self.assertEqual(summary["total_runs"], 2)
        self.assertEqual(summary["attacker_win_rate"], 50.0)
        self.assertEqual(summary["defender_win_rate"], 50.0)
        self.assertEqual(summary["detection_rate"], 50.0)
        self.assertEqual(summary["avg_turns"], 4.0)


if __name__ == "__main__":
    unittest.main()
