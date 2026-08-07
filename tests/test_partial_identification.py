"""Tests for Theorem 5.4 partial-identification fallback."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.dgp import SimulationConfig, generate_minimal_archive
from causal_atlas_sim.methods import AtlasConfig
from causal_atlas_sim.partial_identification import (
    PartialIdentificationExperimentConfig,
    PartialIdentificationScenario,
    fit_reject_or_identify,
    oracle_hull_distance,
    run_partial_identification_experiment,
)
from causal_atlas_sim.reporting import build_artifact_manifest


class PartialIdentificationTests(unittest.TestCase):
    def test_interval_is_the_intersection_of_allocated_component_intervals(self) -> None:
        generated = generate_minimal_archive(seed=901)
        result = fit_reject_or_identify(
            generated.archive,
            generated.target,
            AtlasConfig(zeta=0.05),
            max_singletons=2,
        )
        interval = result.partial_interval
        self.assertEqual(len(interval.weights), 4)
        self.assertAlmostEqual(interval.component_zeta, 0.05 / 4.0)
        self.assertAlmostEqual(
            interval.interval_lower,
            max(
                center - radius
                for center, radius in zip(
                    interval.centers, interval.radii, strict=True
                )
            ),
        )
        self.assertAlmostEqual(
            interval.interval_upper,
            min(
                center + radius
                for center, radius in zip(
                    interval.centers, interval.radii, strict=True
                )
            ),
        )
        self.assertTrue(
            all(
                np.all(weights >= -1e-12)
                and np.isclose(weights.sum(), 1.0)
                for weights in interval.weights
            )
        )
        self.assertLessEqual(interval.width, interval.reference_width)

    def test_certified_partial_interval_covers_a_strong_mismatch_target(self) -> None:
        generated = generate_minimal_archive(
            SimulationConfig(target_shift_fraction=0.80),
            seed=902,
        )
        result = fit_reject_or_identify(
            generated.archive,
            generated.target,
        )
        self.assertTrue(
            result.partial_interval.contains(generated.target.true_effect)
        )

    def test_oracle_hull_distance_is_zero_for_supported_target(self) -> None:
        generated = generate_minimal_archive(seed=903)
        self.assertLess(
            oracle_hull_distance(generated.archive, generated.target),
            1e-7,
        )

    def test_multi_seed_protocol_has_expected_rows_and_is_deterministic(self) -> None:
        config = PartialIdentificationExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(904, 905),
            scenarios=(
                PartialIdentificationScenario("nominal", "nominal", 0.0),
                PartialIdentificationScenario("stress", "stress", 0.60),
            ),
            max_singletons=2,
        )
        first = run_partial_identification_experiment(config)
        second = run_partial_identification_experiment(config)
        self.assertEqual(len(first.records), 8)
        self.assertEqual(len(first.rows), 2)
        self.assertTrue(all(row.repetitions == 4 for row in first.rows))
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_manifest_includes_stage_nine_artifacts(self) -> None:
        manifest = build_artifact_manifest(PROJECT_ROOT)
        paths = {artifact["path"] for artifact in manifest["artifacts"]}
        self.assertTrue(
            {
                "results/partial_identification_summary.csv",
                "results/partial_identification_seed_summary.csv",
                "results/partial_identification_metadata.json",
                "results/figures/partial_identification_overview.png",
                "results/tables/partial_identification_tables.md",
            }.issubset(paths)
        )
        self.assertEqual(
            manifest["result_row_counts"][
                "partial_identification_summary.csv"
            ],
            4,
        )


if __name__ == "__main__":
    unittest.main()
