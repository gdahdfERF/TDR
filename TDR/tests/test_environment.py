"""
Tests for Simulated Environment (V0.2).
Verifies suspicion math, decay, evidence accumulation, detection threshold, and false positive containment.
"""

import math
import unittest
from src.environment.simple_env import SimpleEnvironment


class TestSimpleEnvironment(unittest.TestCase):
    def test_suspicion_calculation(self):
        """Verify that attacker actions increment suspicion by defined deltas."""
        env = SimpleEnvironment(seed=42)
        self.assertEqual(env.suspicion_level, 0.0)

        # Execute scan (+0.30)
        success, _ = env.execute_attacker_action("scan")
        self.assertTrue(success)
        self.assertTrue(math.isclose(env.suspicion_level, 0.30, abs_tol=1e-3))

        # Execute login (+0.35)
        success, _ = env.execute_attacker_action("login")
        self.assertTrue(success)
        self.assertTrue(math.isclose(env.suspicion_level, 0.65, abs_tol=1e-3))

    def test_access_resource_suspicion_increment(self):
        """Verify that access_resource adds +0.40 rather than forcing an automatic 1.0."""
        env = SimpleEnvironment(seed=42)
        env.execute_attacker_action("scan")   # +0.30 -> 0.30
        env.execute_attacker_action("login")  # +0.35 -> 0.65
        env.execute_attacker_action("access_resource")  # +0.40 -> clamped to 1.0 (0.65 + 0.40 = 1.05 -> 1.0)
        self.assertTrue(env.resource_accessed)
        self.assertTrue(math.isclose(env.suspicion_level, 1.0, abs_tol=1e-3))

        # Test with decay so the sum does NOT reach 1.0
        env2 = SimpleEnvironment(seed=42)
        env2.execute_attacker_action("scan")   # 0.30
        env2.execute_attacker_action("wait")   # 0.30 - 0.15 = 0.15
        env2.execute_attacker_action("login")  # 0.15 + 0.35 = 0.50
        env2.execute_attacker_action("access_resource")  # 0.50 + 0.40 = 0.90 (NOT 1.0!)
        self.assertTrue(math.isclose(env2.suspicion_level, 0.90, abs_tol=1e-3))
        self.assertLess(env2.suspicion_level, 1.0)

    def test_suspicion_decay(self):
        """Verify that 'wait' action decays suspicion by 0.15 and bounds at 0.0."""
        env = SimpleEnvironment(seed=42)
        env.execute_attacker_action("scan")  # 0.30
        env.execute_attacker_action("wait")  # 0.30 - 0.15 = 0.15
        self.assertTrue(math.isclose(env.suspicion_level, 0.15, abs_tol=1e-3))

        # Decay again -> 0.0
        env.execute_attacker_action("wait")
        self.assertTrue(math.isclose(env.suspicion_level, 0.0, abs_tol=1e-3))

        # Extra wait does not go negative
        env.execute_attacker_action("wait")
        self.assertEqual(env.suspicion_level, 0.0)

    def test_benign_background_noise(self):
        """Verify start_turn adds between 0.02 and 0.08 benign noise."""
        env = SimpleEnvironment(seed=42)
        initial = env.suspicion_level
        env.start_turn(turn=1)
        noise_added = env.suspicion_level - initial
        self.assertGreaterEqual(noise_added, 0.02)
        self.assertLessEqual(noise_added, 0.08)
        self.assertGreater(len(env.recent_logs), 0)

    def test_prerequisites(self):
        """Verify login requires scan, and access_resource requires login."""
        env = SimpleEnvironment(seed=42)

        # Attempt login without scan
        success, msg = env.execute_attacker_action("login")
        self.assertFalse(success)
        self.assertFalse(env.authenticated)

        # Attempt access without login
        env.execute_attacker_action("scan")
        success, msg = env.execute_attacker_action("access_resource")
        self.assertFalse(success)
        self.assertFalse(env.resource_accessed)

    def test_evidence_accumulation_and_threshold(self):
        """Verify evidence accumulates as suspicion * 0.60 and triggers detection at 0.70."""
        env = SimpleEnvironment(seed=42)
        env.start_turn(turn=1)
        env.suspicion_level = 0.50

        # Investigate: gain = 0.50 * 0.60 = 0.30
        env.execute_defender_action("investigate")
        self.assertTrue(math.isclose(env.evidence_score, 0.30, abs_tol=1e-3))
        self.assertFalse(env.detected)

        # Second investigation with suspicion at 0.80: gain = 0.80 * 0.60 = 0.48
        # Total evidence = 0.30 + 0.48 = 0.78 >= 0.70 threshold -> Detected!
        env.start_turn(turn=2)
        env.suspicion_level = 0.80
        env.execute_defender_action("investigate")
        self.assertGreaterEqual(env.evidence_score, 0.70)
        self.assertTrue(env.detected)
        self.assertEqual(env.detection_turn, 2)

    def test_false_positive_containment(self):
        """Verify blocking with insufficient evidence (< 0.70) records false positive and does not block."""
        env = SimpleEnvironment(seed=42)
        env.evidence_score = 0.40  # Below 0.70

        success, msg = env.execute_defender_action("block")
        self.assertFalse(success)
        self.assertFalse(env.is_blocked)
        self.assertTrue(env.false_positive)
        self.assertEqual(env.false_positive_count, 1)

    def test_valid_containment(self):
        """Verify blocking with sufficient evidence (>= 0.70) successfully blocks intruder."""
        env = SimpleEnvironment(seed=42)
        env.evidence_score = 0.75

        success, msg = env.execute_defender_action("block")
        self.assertTrue(success)
        self.assertTrue(env.is_blocked)
        self.assertEqual(env.containment_turn, env.current_turn)


if __name__ == "__main__":
    unittest.main()
