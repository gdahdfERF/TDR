"""
Main Execution Script for AI Cybersecurity Simulation (V1.0).

Supports both Rule-Based and real Gemini-powered LLM Attacker Agents:
  Rule-based baseline:  python main.py --attacker-type rule --seed 42
  Gemini LLM single:    python main.py --attacker-type llm --seed 42
  Gemini LLM batch:     python main.py --attacker-type llm --runs 20 --seed 42
"""

import argparse
import os
import random
from src.environment.simple_env import SimpleEnvironment
from src.agents.attacker.attacker_agent import RuleBasedAttacker
from src.agents.attacker.llm_attacker import LLMAttacker
from src.agents.defender.defender_agent import RuleBasedDefender
from src.simulation.engine import SimulationEngine
from src.telemetry.logger import SimpleLogger
from src.telemetry.metrics import MetricsCollector

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Cybersecurity Simulation Framework (V1.0 - Gemini LLM Integration)"
    )
    parser.add_argument(
        "--attacker-type",
        type=str,
        default="rule",
        choices=["rule", "llm"],
        help="Attacker agent type: 'rule' (RuleBasedAttacker) or 'llm' (Gemini Flash LLMAttacker)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3.1-flash-lite",
        help="Gemini model to use for LLMAttacker (e.g., 'gemini-3.1-flash-lite', 'gemini-3.8-flash')",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Gemini API Key (optional, defaults to GEMINI_API_KEY environment variable)",
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use offline mock generator for LLMAttacker (useful for testing without API keys)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of simulation episodes to execute",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=15,
        help="Maximum number of turns per episode",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible experiments",
    )
    parser.add_argument(
        "--attacker-strategy",
        type=str,
        default="adaptive",
        choices=["adaptive", "aggressive", "stealth"],
        help="Strategy profile for Rule-Based Attacker AI (if --attacker-type rule)",
    )
    parser.add_argument(
        "--stealth",
        type=float,
        default=0.3,
        help="Attacker stealth wait bias (0.0 to 1.0)",
    )
    parser.add_argument(
        "--defender-policy",
        type=str,
        default="balanced",
        choices=["balanced", "cautious", "aggressive"],
        help="Policy profile for Defender AI",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress turn-by-turn logs during batch runs",
    )
    return parser.parse_args()


def run_single_simulation(args, seed=None, verbose=True):
    """Execute one simulation episode."""
    env = SimpleEnvironment(seed=seed, max_turns=args.max_turns)

    if args.attacker_type == "llm":
        attacker = LLMAttacker(
            model=args.model,
            api_key=args.api_key,
            mock_fallback=args.mock_llm,
            seed=seed,  # seed mock RNG so runs are reproducible but differ from rule-based
        )
    else:
        attacker = RuleBasedAttacker(
            strategy=args.attacker_strategy,
            stealth_bias=args.stealth,
            seed=seed,
        )

    defender = RuleBasedDefender(policy=args.defender_policy)
    logger = SimpleLogger(log_file="data/logs/simulation.jsonl", verbose=verbose)

    engine = SimulationEngine(
        env=env,
        attacker=attacker,
        defender=defender,
        logger=logger,
        max_turns=args.max_turns,
        seed=seed,
    )
    return engine.run()


def check_api_key_status(args):
    """Notify user if LLM attacker is selected without an API key."""
    if args.attacker_type == "llm" and not args.mock_llm:
        has_key = bool(args.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        if not has_key:
            print("\n" + "!" * 70)
            print(" [WARNING] No GEMINI_API_KEY found in environment or .env file.")
            print(" LLMAttacker will trigger the fallback mechanism and return 'wait'.")
            print(" To run with live Gemini Flash, set your key:")
            print("   Windows PowerShell:  $env:GEMINI_API_KEY=\"your_key_here\"")
            print("   Or create a .env file: GEMINI_API_KEY=your_key_here")
            print("   Or use:              python main.py --attacker-type llm --api-key \"your_key\"")
            print("   Or offline test:     python main.py --attacker-type llm --mock-llm")
            print("!" * 70 + "\n")


def main():
    args = parse_args()
    check_api_key_status(args)

    attacker_label = f"LLM ({args.model})" if args.attacker_type == "llm" else f"RULE ({args.attacker_strategy.upper()})"

    if args.runs <= 1:
        # ----------------------------------------------------
        # Single Run Mode
        # ----------------------------------------------------
        print("=" * 70)
        print("      AI CYBERSECURITY SIMULATION - V1.0")
        print(f"      Attacker: {attacker_label} | Defender: {args.defender_policy.upper()} | Seed: {args.seed}")
        print("=" * 70)

        results = run_single_simulation(args, seed=args.seed, verbose=not args.quiet)

        print("\n" + "=" * 70)
        print("                     SIMULATION RESULTS")
        print("=" * 70)
        print(f"Winner:              {results['winner']}")
        print(f"Number of turns:     {results['total_turns']}")
        print(f"Attack success:      {results['attack_success']}")
        print(f"Detection status:    {'Detected' if results['detected'] else 'Undetected'}")
        print(f"Detection turn:      {results['detection_turn']}")
        print(f"Containment turn:    {results['containment_turn']}")
        print(f"False positive:      {results['false_positive']}")
        print(f"Final suspicion:     {results['final_suspicion']:.3f}")
        print(f"Final evidence:      {results['final_evidence']:.3f}")
        print("=" * 70)
        print("Detailed log saved to: data/logs/simulation.jsonl\n")

    else:
        # ----------------------------------------------------
        # Multi-Run Batch Evaluation Mode
        # ----------------------------------------------------
        print("=" * 70)
        print(f"   BATCH SIMULATION EXPERIMENT ({args.runs} RUNS) - V1.0")
        print(f"   Attacker: {attacker_label} | Defender: {args.defender_policy.upper()} | Master Seed: {args.seed}")
        print("=" * 70)

        # Generate deterministic sequence of subseeds if master seed provided
        if args.seed is not None:
            master_rng = random.Random(args.seed)
            subseeds = [master_rng.randint(1000, 999_999) for _ in range(args.runs)]
        else:
            subseeds = [None] * args.runs

        collector = MetricsCollector(output_dir="data/results")

        for run_id, run_seed in enumerate(subseeds, start=1):
            verbose = (not args.quiet) and (args.runs <= 3)
            if verbose:
                print(f"\n--- Starting Run {run_id}/{args.runs} (Seed: {run_seed}) ---")
            res = run_single_simulation(args, seed=run_seed, verbose=verbose)
            collector.record_run(run_id, res)

        summary = collector.compute_summary()
        strategy_suffix = f"_{args.attacker_strategy}" if args.attacker_type == "rule" else ""
        csv_filename = f"benchmark_metrics_{args.attacker_type}{strategy_suffix}.csv"
        csv_path = collector.export_to_csv(csv_filename)

        print("\n" + "=" * 70)
        print(f"            AGGREGATED EXPERIMENT SUMMARY ({summary['total_runs']} RUNS)")
        print(f"            Attacker: {attacker_label} vs Defender: {args.defender_policy.upper()}")
        print("=" * 70)
        print(f"Attacker Win Rate:        {summary['attacker_win_rate']:6.2f}% ({summary['attacker_wins']}/{summary['total_runs']})")
        print(f"Defender Win Rate:        {summary['defender_win_rate']:6.2f}% ({summary['defender_wins']}/{summary['total_runs']})")
        print(f"Draw / Timeout Rate:      {summary['draw_rate']:6.2f}% ({summary['draws']}/{summary['total_runs']})")
        print(f"Detection Rate:           {summary['detection_rate']:6.2f}%")
        print(f"False-Positive Rate:      {summary['false_positive_rate']:6.2f}%")
        det_str = f"{summary['avg_detection_turn']:.2f}" if summary['avg_detection_turn'] else "N/A"
        cnt_str = f"{summary['avg_containment_turn']:.2f}" if summary['avg_containment_turn'] else "N/A"
        print(f"Average Detection Turn:   {det_str}")
        print(f"Average Containment Turn: {cnt_str}")
        print(f"Average Number of Turns:  {summary['avg_turns']:.2f}")
        print("=" * 70)
        print(f"Metrics saved to:         {csv_path}\n")


if __name__ == "__main__":
    main()
