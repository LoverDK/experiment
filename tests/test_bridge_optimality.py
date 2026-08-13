"""Tests for the small-library exhaustive bridge benchmark."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.bridge_experiment import run_bridge_optimality_experiment


class BridgeOptimalityTests(unittest.TestCase):
    def test_greedy_is_compared_with_exhaustive_optimum(self) -> None:
        rows = run_bridge_optimality_experiment(
            repetitions=2,
            base_seed=303,
            budgets=(1, 2),
        )
        self.assertEqual([row.budget for row in rows], [1, 2])
        self.assertEqual([row.exhaustive_sets_per_repetition for row in rows], [12, 66])
        self.assertTrue(all(row.optimal_mean_final_diameter <= row.greedy_mean_final_diameter + 1e-10 for row in rows))


if __name__ == "__main__":
    unittest.main()
