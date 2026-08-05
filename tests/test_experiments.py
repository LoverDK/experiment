"""Tests for the fixed-seed main simulation protocol."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim import (
    MainExperimentConfig,
    SimulationConfig,
    SweepDefinition,
    generate_minimal_archive,
    minimal_assumption_report,
    run_main_experiment,
)


class MainExperimentTests(unittest.TestCase):
    def test_semantic_mismatch_stays_inside_the_certified_dgp(self) -> None:
        generated = generate_minimal_archive(
            SimulationConfig(target_shift_fraction=0.25), seed=303
        )
        report = minimal_assumption_report(generated)
        self.assertTrue(all(item["satisfied"] for item in report.values()))
        self.assertGreater(generated.support_residual(), 0.0)

    def test_protocol_produces_one_row_per_method_and_level(self) -> None:
        config = MainExperimentConfig(
            repetitions=3,
            base_seed=811,
            methods=("atlas", "global_mean"),
            sweeps=(
                SweepDefinition(
                    "semantic_shift_fraction",
                    "semantic mismatch fraction",
                    (0.0, 0.25),
                ),
                SweepDefinition(
                    "scientific_tolerance",
                    "scientific tolerance",
                    (1.25, 1.65),
                ),
            ),
        )
        result = run_main_experiment(config)
        self.assertEqual(len(result.rows), 8)
        self.assertEqual({row.method for row in result.rows}, set(config.methods))
        self.assertEqual(
            {row.sweep_key for row in result.rows},
            {"semantic_shift_fraction", "scientific_tolerance"},
        )

    def test_protocol_is_deterministic_for_fixed_seeds(self) -> None:
        config = MainExperimentConfig(
            repetitions=3,
            base_seed=812,
            methods=("atlas",),
            sweeps=(
                SweepDefinition(
                    "moderator_sensitivity_radius",
                    "hidden moderator sensitivity radius",
                    (0.20, 0.40),
                ),
            ),
        )
        first = run_main_experiment(config).to_dict()
        second = run_main_experiment(config).to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
