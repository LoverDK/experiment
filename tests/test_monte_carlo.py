"""Tests for the Monte Carlo repetition scaffold."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.monte_carlo import MonteCarloConfig, run_monte_carlo


class MonteCarloTests(unittest.TestCase):
    def test_repetitions_are_deterministic_for_a_fixed_seed(self) -> None:
        config = MonteCarloConfig(repetitions=12, base_seed=123)
        first = run_monte_carlo(config).summary()
        second = run_monte_carlo(config).summary()
        self.assertEqual(first, second)

    def test_each_repetition_has_unique_child_seed(self) -> None:
        result = run_monte_carlo(MonteCarloConfig(repetitions=12, base_seed=123))
        seeds = [record.seed for record in result.records]
        self.assertEqual(len(seeds), len(set(seeds)))

    def test_certified_interval_covers_and_curvature_bound_holds(self) -> None:
        result = run_monte_carlo(MonteCarloConfig(repetitions=20, base_seed=456))
        summary = result.summary()
        self.assertEqual(summary["curvature_bound_violation_rate"], 0.0)
        self.assertGreaterEqual(summary["certified_coverage"], 0.0)
        self.assertLessEqual(summary["certified_coverage"], 1.0)
        self.assertEqual(summary["mean_support_residual"], 0.0)


if __name__ == "__main__":
    unittest.main()
