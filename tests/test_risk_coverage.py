"""Tests for the selective-prediction risk--coverage protocol."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.risk_coverage import RiskCoverageConfig, run_risk_coverage_experiment


class RiskCoverageTests(unittest.TestCase):
    def test_endpoint_is_no_rejection_on_shared_draws(self) -> None:
        result = run_risk_coverage_experiment(
            RiskCoverageConfig(
                repetitions_per_seed=4,
                base_seeds=(11, 12),
                thresholds=(1.0, 1.65, 2.5),
            )
        )
        self.assertEqual(len(result.rows), 4)
        self.assertEqual(result.rows[-1].acceptance_rate, 1.0)
        self.assertAlmostEqual(
            result.rows[-1].conditional_mae,
            result.rows[-1].unconditional_mae,
        )
        rates = [row.acceptance_rate for row in result.rows]
        self.assertEqual(rates, sorted(rates))

    def test_protocol_is_deterministic(self) -> None:
        config = RiskCoverageConfig(repetitions_per_seed=3, base_seeds=(13,), thresholds=(1.0, 2.0))
        self.assertEqual(run_risk_coverage_experiment(config).to_dict(), run_risk_coverage_experiment(config).to_dict())


if __name__ == "__main__":
    unittest.main()
