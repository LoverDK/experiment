"""Tests for the multi-seed formal experiment layer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.formal_experiment import (
    FormalEstimator,
    FormalExperimentConfig,
    FormalScenario,
    default_formal_estimators,
    run_formal_experiment,
    wilson_interval,
)


class FormalExperimentTests(unittest.TestCase):
    def test_default_estimators_include_main_ablation_and_baselines(self) -> None:
        keys = {estimator.key for estimator in default_formal_estimators()}
        self.assertEqual(
            keys,
            {
                "atlas",
                "atlas_no_rejection",
                "atlas_no_variance_penalty",
                "atlas_top4_candidates",
                "semantic_forced",
                "nearest_semantic",
                "global_mean",
            },
        )

    def test_multi_seed_rows_pool_expected_repetitions(self) -> None:
        config = FormalExperimentConfig(
            repetitions_per_seed=3,
            base_seeds=(901, 902),
            scenarios=(
                FormalScenario("nominal", "nominal setting"),
            ),
            estimators=(
                FormalEstimator("atlas", "atlas"),
                FormalEstimator("global_mean", "global_mean"),
            ),
        )
        result = run_formal_experiment(config)
        self.assertEqual(len(result.records), 12)
        self.assertEqual(len(result.rows), 2)
        self.assertTrue(all(row.repetitions == 6 for row in result.rows))
        self.assertTrue(all(row.seed_batches == 2 for row in result.rows))

    def test_formal_run_is_deterministic(self) -> None:
        config = FormalExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(903, 904),
            scenarios=(
                FormalScenario(
                    "stress",
                    "stress",
                    semantic_shift_fraction=0.10,
                ),
            ),
            estimators=(FormalEstimator("atlas", "atlas"),),
        )
        first = run_formal_experiment(config).to_dict()
        second = run_formal_experiment(config).to_dict()
        self.assertEqual(first, second)
        self.assertIn("dgp_config", first["config"])
        self.assertIn("atlas_config", first["config"])

    def test_wilson_interval_handles_boundary_counts(self) -> None:
        zero_lower, zero_upper = wilson_interval(0, 300)
        one_lower, one_upper = wilson_interval(300, 300)
        self.assertEqual(zero_lower, 0.0)
        self.assertGreater(zero_upper, 0.0)
        self.assertLess(one_lower, 1.0)
        self.assertEqual(one_upper, 1.0)


if __name__ == "__main__":
    unittest.main()
