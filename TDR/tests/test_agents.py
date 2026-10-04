"""
Tests for Attacker and Defender Agents (V0.2).
Verifies BaseAgent interface conformance, strategy execution, and policy responses.
"""

import unittest
from src.agents.base_agent import BaseAgent
from src.agents.attacker.attacker_agent import RuleBasedAttacker
from src.agents.attacker.llm_attacker import LLMAttacker
from src.agents.defender.defender_agent import RuleBasedDefender


class TestAgents(unittest.TestCase):
    def test_agent_interface_conformance(self):
        """Verify agents inherit from BaseAgent and implement lifecycle methods."""
        att = RuleBasedAttacker()
        def_agent = RuleBasedDefender()

        self.assertIsInstance(att, BaseAgent)
        self.assertIsInstance(def_agent, BaseAgent)
        self.assertEqual(att.role, "ATTACKER")
        self.assertEqual(def_agent.role, "DEFENDER")

    def test_attacker_aggressive_progression(self):
        """Verify aggressive attacker progresses scan -> login -> access without waiting."""
        att = RuleBasedAttacker(strategy="aggressive")

        # Step 1
        action1 = att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action1, "scan")

        # Step 2
        action2 = att.select_action({"scanned": True, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action2, "login")

        # Step 3
        action3 = att.select_action({"scanned": True, "authenticated": True, "resource_accessed": False})
        self.assertEqual(action3, "access_resource")

    def test_attacker_stealth_waiting(self):
        """Verify stealth attacker inserts wait after loud actions when turn slack exists."""
        att = RuleBasedAttacker(strategy="stealth")

        # Turn 1: scan
        action1 = att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False, "current_turn": 1, "max_turns": 15})
        self.assertEqual(action1, "scan")

        # Turn 2: should wait because it just scanned and has slack
        action2 = att.select_action({"scanned": True, "authenticated": False, "resource_accessed": False, "current_turn": 2, "max_turns": 15})
        self.assertEqual(action2, "wait")

    def test_defender_action_selection(self):
        """Verify defender chooses monitor, investigate, or block based on observations."""
        defender = RuleBasedDefender(policy="balanced")

        # Clean baseline -> monitor
        action1 = defender.select_action({"observed_suspicion": 0.05, "evidence_score": 0.0, "is_detected": False, "recent_logs": []})
        self.assertEqual(action1, "monitor")

        # Elevated suspicion -> investigate
        action2 = defender.select_action({"observed_suspicion": 0.40, "evidence_score": 0.2, "is_detected": False, "recent_logs": []})
        self.assertEqual(action2, "investigate")

        # Verified evidence -> block
        action3 = defender.select_action({"observed_suspicion": 0.60, "evidence_score": 0.75, "is_detected": True, "recent_logs": []})
        self.assertEqual(action3, "block")

    def test_defender_aggressive_triggers_early_block(self):
        """Verify aggressive defender policy can trigger premature block (false positive scenario)."""
        defender = RuleBasedDefender(policy="aggressive")

        # High suspicion (0.65) but low evidence (0.30)
        action = defender.select_action({
            "observed_suspicion": 0.65,
            "evidence_score": 0.30,
            "is_detected": False,
            "recent_logs": []
        })
        self.assertEqual(action, "block")

    def test_llm_attacker_fallback_missing_key(self):
        """Verify LLMAttacker falls back to 'wait' when no API key is provided."""
        llm_att = LLMAttacker(api_key=None, mock_fallback=False)
        llm_att.client = None
        action = llm_att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action, "wait")
        self.assertIn("API Error", llm_att.last_reasoning)

    def test_llm_attacker_fallback_timeout(self):
        """Verify LLMAttacker falls back to 'wait' on TimeoutError."""
        llm_att = LLMAttacker(api_key="dummy_key", mock_fallback=False)
        class MockClientTimeout:
            class models:
                @staticmethod
                def generate_content(*args, **kwargs):
                    raise TimeoutError("Connection to Gemini timed out.")
        llm_att.client = MockClientTimeout()
        action = llm_att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action, "wait")
        self.assertIn("Timeout", llm_att.last_reasoning)

    def test_llm_attacker_fallback_api_error(self):
        """Verify LLMAttacker falls back to 'wait' on general API error."""
        llm_att = LLMAttacker(api_key="dummy_key", mock_fallback=False)
        class MockClientError:
            class models:
                @staticmethod
                def generate_content(*args, **kwargs):
                    raise RuntimeError("Gemini API quota exceeded (429).")
        llm_att.client = MockClientError()
        action = llm_att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action, "wait")
        self.assertIn("API Error", llm_att.last_reasoning)

    def test_llm_attacker_fallback_invalid_response(self):
        """Verify LLMAttacker falls back to 'wait' if response has invalid schema or hallucinated action."""
        llm_att = LLMAttacker(api_key="dummy_key", mock_fallback=False)
        class MockResponse:
            text = '{"reasoning": "I want to launch DDoS", "action": "ddos_attack"}'
        class MockClientInvalid:
            class models:
                @staticmethod
                def generate_content(*args, **kwargs):
                    return MockResponse()
        llm_att.client = MockClientInvalid()
        action = llm_att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action, "wait")
        self.assertIn("API Error", llm_att.last_reasoning)

    def test_llm_attacker_valid_response(self):
        """Verify LLMAttacker extracts and returns action when Gemini returns valid structured JSON."""
        llm_att = LLMAttacker(api_key="dummy_key", mock_fallback=False)
        class MockResponse:
            text = '{"reasoning": "Target is not scanned yet. Need recon.", "action": "scan"}'
        class MockClientValid:
            class models:
                @staticmethod
                def generate_content(*args, **kwargs):
                    return MockResponse()
        llm_att.client = MockClientValid()
        action = llm_att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(action, "scan")
        self.assertEqual(llm_att.last_reasoning, "Target is not scanned yet. Need recon.")

    def test_llm_attacker_mock_offline_mode(self):
        """Verify mock_fallback produces sequential actions when offline testing is desired."""
        llm_att = LLMAttacker(api_key=None, mock_fallback=True)
        act1 = llm_att.select_action({"scanned": False, "authenticated": False, "resource_accessed": False})
        self.assertEqual(act1, "scan")

        act2 = llm_att.select_action({"scanned": True, "authenticated": False, "resource_accessed": False})
        self.assertEqual(act2, "login")

        act3 = llm_att.select_action({"scanned": True, "authenticated": True, "resource_accessed": False})
        self.assertEqual(act3, "access_resource")


if __name__ == "__main__":
    unittest.main()

