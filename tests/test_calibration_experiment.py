"""Tests for certificate calibration and failure-boundary summaries."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.calibration_experiment import (
    CalibrationExperimentConfig,
    CalibrationPolicy,
    CalibrationScenario,
    default_calibration_policies,
    run_calibration_experiment,
)


class CalibrationExperimentTests(unittest.TestCase):
    def test_default_policies_cover_certified_rejection_and_misspecification(self) -> None:
        self.assertEqual(
            {policy.key for policy in default_calibration_policies()},
            {"certified_atlas", "no_rejection", "understated_smoothness"},
        )

    def test_shared_multiseed_protocol_has_expected_rows(self) -> None:
        config = CalibrationExperimentConfig(
            repetitions_per_seed=3,
            base_seeds=(1001, 1002),
            scenarios=(
                CalibrationScenario("nominal", "nominal"),
            ),
            policies=(
                CalibrationPolicy("certified_atlas", "certified ATLAS", "atlas"),
                CalibrationPolicy(
                    "no_rejection",
                    "no rejection",
                    "atlas_no_rejection",
                ),
            ),
        )
        result = run_calibration_experiment(config)
        self.assertEqual(len(result.records), 12)
        self.assertEqual(len(result.rows), 2)
        self.assertTrue(all(row.repetitions == 6 for row in result.rows))
        self.assertTrue(all(row.seed_batches == 2 for row in result.rows))

    def test_protocol_is_deterministic(self) -> None:
        config = CalibrationExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(1003, 1004),
            scenarios=(
                CalibrationScenario(
                    "stress",
                    "stress",
                    semantic_shift_fraction=0.60,
                ),
            ),
            policies=(
                CalibrationPolicy(
                    "understated_smoothness",
                    "understated",
                    "atlas",
                    effect_lipschitz_bound=0.20,
                    effect_curvature_bound=0.05,
                ),
            ),
        )
        self.assertEqual(
            run_calibration_experiment(config).to_dict(),
            run_calibration_experiment(config).to_dict(),
        )


if __name__ == "__main__":
    unittest.main()
