"""Tests for the two-dimensional representation-sensitivity protocol."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.representation_sensitivity import (
    RepresentationSensitivityConfig,
    run_representation_sensitivity,
)


class RepresentationSensitivityTests(unittest.TestCase):
    def test_grid_uses_paired_fixed_seed_protocol(self) -> None:
        config = RepresentationSensitivityConfig(
            repetitions_per_seed=2,
            base_seeds=(701,),
            hidden_shift_fractions=(0.0, 0.8),
            proxy_uncertainties=(0.05, 0.40),
        )
        result = run_representation_sensitivity(config)
        self.assertEqual(len(result.records), 8)
        self.assertEqual(len(result.rows), 4)
        self.assertEqual(
            {(row.hidden_shift_fraction, row.proxy_uncertainty) for row in result.rows},
            {(0.0, 0.05), (0.0, 0.40), (0.8, 0.05), (0.8, 0.40)},
        )
        self.assertTrue(
            all(
                row.representation_advantage
                == row.semantic_forced_mae - row.atlas_no_rejection_mae
                for row in result.rows
            )
        )

    def test_run_is_deterministic(self) -> None:
        config = RepresentationSensitivityConfig(
            repetitions_per_seed=2,
            base_seeds=(702,),
            hidden_shift_fractions=(0.4,),
            proxy_uncertainties=(0.20,),
        )
        first = run_representation_sensitivity(config).to_dict()
        second = run_representation_sensitivity(config).to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
