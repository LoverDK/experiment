"""Tests for the Theorem 5.5 minimax lower-bound experiment."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.minimax_experiment import (
    MinimaxExperimentConfig,
    MinimaxScenario,
    default_minimax_scenarios,
    geometric_surface_value,
    minimax_parameters,
    run_minimax_experiment,
)
from causal_atlas_sim.reporting import build_artifact_manifest


class MinimaxExperimentTests(unittest.TestCase):
    def test_default_protocol_crosses_four_distances_with_two_noise_levels(
        self,
    ) -> None:
        scenarios = default_minimax_scenarios()
        self.assertEqual(len(scenarios), 8)
        self.assertSetEqual(
            {scenario.hull_distance for scenario in scenarios},
            {0.0, 0.25, 0.60, 1.0},
        )
        self.assertSetEqual(
            {scenario.archive_standard_error for scenario in scenarios},
            {0.35, 1.20},
        )

    def test_geometric_pair_agrees_on_archive_and_respects_the_bounds(self) -> None:
        scenario = MinimaxScenario("test", "test", 0.5, 1.0)
        config = MinimaxExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(1,),
            scenarios=(scenario,),
            archive_count=4,
        )
        parameters = minimax_parameters(scenario, config)
        positive_archive = geometric_surface_value(0.0, scenario, parameters, 1)
        negative_archive = geometric_surface_value(0.0, scenario, parameters, -1)
        positive_target = geometric_surface_value(0.5, scenario, parameters, 1)
        negative_target = geometric_surface_value(0.5, scenario, parameters, -1)

        self.assertEqual(positive_archive, 0.0)
        self.assertEqual(negative_archive, 0.0)
        self.assertAlmostEqual(positive_target, -negative_target)
        self.assertAlmostEqual(
            positive_target,
            0.25 * min(config.effect_lipschitz_bound * 0.5, 3.88),
        )
        self.assertLessEqual(
            positive_target / scenario.hull_distance,
            config.effect_lipschitz_bound,
        )
        self.assertLessEqual(abs(positive_target), config.effect_absolute_bound)

    def test_information_and_le_cam_components_match_theorem_construction(self) -> None:
        scenario = MinimaxScenario("test", "test", 0.0, 1.0)
        config = MinimaxExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(2,),
            scenarios=(scenario,),
            archive_count=4,
            le_cam_constant=0.25,
        )
        parameters = minimax_parameters(scenario, config)
        self.assertAlmostEqual(parameters.information, 4.0)
        self.assertAlmostEqual(parameters.estimator_standard_error, 0.5)
        self.assertAlmostEqual(parameters.information_scale, 0.5)
        self.assertAlmostEqual(parameters.statistical_alternative_magnitude, 0.125)
        self.assertAlmostEqual(parameters.statistical_lower_bound, 0.046875)
        self.assertAlmostEqual(
            parameters.combined_lower_bound,
            parameters.statistical_lower_bound,
        )

    def test_multi_seed_protocol_is_deterministic_and_analytic_risk_dominates_bound(
        self,
    ) -> None:
        config = MinimaxExperimentConfig(
            repetitions_per_seed=3,
            base_seeds=(31, 32),
            scenarios=(
                MinimaxScenario("supported", "supported", 0.0, 0.5),
                MinimaxScenario("unsupported", "unsupported", 0.6, 1.0),
            ),
            archive_count=4,
        )
        first = run_minimax_experiment(config)
        second = run_minimax_experiment(config)
        self.assertEqual(len(first.records), 12)
        self.assertEqual(len(first.rows), 2)
        self.assertTrue(all(row.repetitions == 6 for row in first.rows))
        self.assertTrue(
            all(
                row.analytic_worst_case_mae >= row.combined_lower_bound
                for row in first.rows
            )
        )
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_manifest_includes_stage_ten_artifacts(self) -> None:
        manifest = build_artifact_manifest(PROJECT_ROOT)
        paths = {artifact["path"] for artifact in manifest["artifacts"]}
        self.assertTrue(
            {
                "results/minimax_experiment_summary.csv",
                "results/minimax_experiment_seed_summary.csv",
                "results/minimax_experiment_metadata.json",
                "results/figures/minimax_experiment_overview.png",
                "results/tables/minimax_experiment_tables.md",
            }.issubset(paths)
        )
        self.assertEqual(
            manifest["result_row_counts"]["minimax_experiment_summary.csv"],
            8,
        )


if __name__ == "__main__":
    unittest.main()
