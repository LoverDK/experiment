"""Tests for fair shared-seed method comparisons."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.comparison import MethodComparisonConfig, run_method_comparison


class ComparisonTests(unittest.TestCase):
    def test_shared_repetitions_are_deterministic(self) -> None:
        config = MethodComparisonConfig(repetitions=8, base_seed=77)
        first = run_method_comparison(config)
        second = run_method_comparison(config)
        self.assertEqual(first.summary(), second.summary())
        self.assertEqual(
            [record.seed for record in first.records],
            [record.seed for record in second.records],
        )

    def test_all_methods_use_the_same_replication_seeds(self) -> None:
        result = run_method_comparison(MethodComparisonConfig(repetitions=8, base_seed=78))
        self.assertEqual(len(result.records), 8)
        self.assertTrue(
            all(set(record.results) == set(result.config.methods) for record in result.records)
        )
        self.assertEqual(len({record.seed for record in result.records}), 8)

    def test_atlas_ablation_and_baselines_are_reported(self) -> None:
        result = run_method_comparison(MethodComparisonConfig(repetitions=8, base_seed=79))
        summary = result.summary()
        for method in result.config.methods:
            self.assertIn(method, summary)
            self.assertIn("rejection_rate", summary[method])
            self.assertIn("interval_coverage", summary[method])
        self.assertGreater(summary["atlas_no_rejection"]["acceptance_rate"], 0.99)
        self.assertGreater(summary["global_mean"]["acceptance_rate"], 0.99)


if __name__ == "__main__":
    unittest.main()
