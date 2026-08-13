"""Tests for confidence-level coverage--width curves."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.calibration_curve import CalibrationCurveConfig, run_calibration_curve_experiment


class CalibrationCurveTests(unittest.TestCase):
    def test_all_policies_and_levels_are_reported(self) -> None:
        config = CalibrationCurveConfig(
            repetitions_per_seed=3,
            base_seeds=(21,),
            confidence_levels=(0.80, 0.95),
        )
        result = run_calibration_curve_experiment(config)
        self.assertEqual(len(result.rows), 10)
        self.assertEqual(len({row.policy for row in result.rows}), 5)
        self.assertTrue(all(row.mean_width > 0.0 for row in result.rows))

    def test_protocol_is_deterministic(self) -> None:
        config = CalibrationCurveConfig(repetitions_per_seed=2, base_seeds=(22,), confidence_levels=(0.90,))
        self.assertEqual(run_calibration_curve_experiment(config).to_dict(), run_calibration_curve_experiment(config).to_dict())


if __name__ == "__main__":
    unittest.main()
