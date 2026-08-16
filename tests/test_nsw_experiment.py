"""Tests for the NSW real-data local-contrast protocol."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.nsw_experiment import (
    NSW_METHODS,
    NSW_SOURCE_SHA256,
    NswExperimentConfig,
    build_nsw_local_archive,
    fit_nsw_method,
    nsw_archive_map_rows,
    nsw_diagnostic_rows,
    nsw_method_error_rows,
    run_nsw_experiment,
)

DATA_PATH = PROJECT_ROOT / "data" / "nsw_dw.dta"


class NswExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.small_config = NswExperimentConfig(
            n_local_objects=32,
            holdout_count=8,
            repetitions_per_seed=2,
            base_seeds=(20261201,),
            max_candidates=12,
            max_weight_iterations=100,
        )
        cls.archive = build_nsw_local_archive(DATA_PATH, cls.small_config)

    def test_committed_source_hash_and_randomized_arm_counts(self) -> None:
        self.assertEqual(
            hashlib.sha256(DATA_PATH.read_bytes()).hexdigest(),
            NSW_SOURCE_SHA256,
        )
        metadata = self.archive.source_metadata
        self.assertEqual(metadata["dataset_rows"], 445)
        self.assertEqual(metadata["treated_rows"], 185)
        self.assertEqual(metadata["control_rows"], 260)

    def test_local_objects_have_both_arms_and_finite_certificates(self) -> None:
        self.assertEqual(len(self.archive.objects), 32)
        for item in self.archive.objects:
            self.assertEqual(item.sample_size, self.small_config.n_neighbors)
            self.assertGreaterEqual(item.treated_count, self.small_config.min_treated)
            self.assertGreaterEqual(item.control_count, self.small_config.min_control)
            self.assertTrue(np.isfinite(item.estimated_effect))
            self.assertGreater(item.standard_error, 0.0)
            self.assertGreater(item.overlap_score, 0.0)
            self.assertLessEqual(item.overlap_score, 1.0)

    def test_target_effect_and_standard_error_do_not_enter_prediction(self) -> None:
        target = self.archive.objects[0]
        sources = self.archive.objects[1:]
        altered = replace(
            target,
            estimated_effect=target.estimated_effect + 1000.0,
            standard_error=target.standard_error + 1000.0,
        )
        original = fit_nsw_method("atlas", sources, target, self.small_config)
        changed = fit_nsw_method("atlas", sources, altered, self.small_config)
        self.assertEqual(original, changed)

    def test_methods_share_targets_and_ablation_shares_point_weights(self) -> None:
        result = run_nsw_experiment(DATA_PATH, self.small_config)
        expected_records = (
            len(NSW_METHODS)
            * self.small_config.holdout_count
            * self.small_config.repetitions_per_seed
        )
        self.assertEqual(len(result.records), expected_records)
        self.assertEqual(len(result.rows), len(NSW_METHODS))
        map_rows = nsw_archive_map_rows(result)
        diagnostic_rows = nsw_diagnostic_rows(result)
        method_error_rows = nsw_method_error_rows(result)
        self.assertEqual(len(map_rows), self.small_config.n_local_objects)
        self.assertEqual(
            len(diagnostic_rows),
            self.small_config.holdout_count
            * self.small_config.repetitions_per_seed,
        )
        self.assertEqual(len(method_error_rows), expected_records)
        self.assertSetEqual(
            {row.method for row in method_error_rows},
            set(NSW_METHODS),
        )
        self.assertTrue(
            all(row.absolute_reconstruction_error >= 0.0 for row in method_error_rows)
        )
        self.assertTrue(all(np.isfinite(row.pc1) for row in map_rows))
        grouped = {}
        for record in result.records:
            key = (record.replicate, record.target_object_id)
            grouped.setdefault(key, {})[record.method] = record.prediction
        self.assertTrue(grouped)
        for predictions in grouped.values():
            self.assertSetEqual(set(predictions), set(NSW_METHODS))
            self.assertAlmostEqual(
                predictions["atlas"].predicted_effect,
                predictions["atlas_no_rejection"].predicted_effect,
                places=12,
            )

    def test_fixed_protocol_is_deterministic(self) -> None:
        first = run_nsw_experiment(DATA_PATH, self.small_config)
        second = run_nsw_experiment(DATA_PATH, self.small_config)
        self.assertEqual(
            [row.as_dict() for row in first.rows],
            [row.as_dict() for row in second.rows],
        )

    def test_committed_stage_artifacts_have_expected_shape(self) -> None:
        summary_path = PROJECT_ROOT / "results" / "nsw_experiment_summary.csv"
        seed_path = PROJECT_ROOT / "results" / "nsw_experiment_seed_summary.csv"
        metadata_path = PROJECT_ROOT / "results" / "nsw_experiment_metadata.json"
        method_records_path = PROJECT_ROOT / "results" / "nsw_method_error_records.csv"
        if not summary_path.exists():
            self.skipTest("Stage 12 artifacts have not been generated yet.")
        with summary_path.open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        with seed_path.open(newline="", encoding="utf-8") as source:
            seed_rows = list(csv.DictReader(source))
        with method_records_path.open(newline="", encoding="utf-8") as source:
            method_records = list(csv.DictReader(source))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(seed_rows), 15)
        self.assertEqual(len(method_records), 8_400)
        self.assertEqual({row["method"] for row in rows}, set(NSW_METHODS))
        self.assertEqual(metadata["source"]["source_sha256"], NSW_SOURCE_SHA256)
        self.assertEqual(
            metadata["target_level_outputs"]["method_error_rows"],
            8_400,
        )
        for summary in rows:
            method_errors = np.asarray(
                [
                    float(record["absolute_reconstruction_error"])
                    for record in method_records
                    if record["method"] == summary["method"]
                ]
            )
            self.assertEqual(len(method_errors), 1_680)
            self.assertAlmostEqual(
                float(method_errors.mean()),
                float(summary["mae"]),
                places=12,
            )
            self.assertAlmostEqual(
                float(np.median(method_errors)),
                float(summary["median_absolute_error"]),
                places=12,
            )

    def test_manifest_includes_source_and_stage_twelve_artifacts(self) -> None:
        manifest = json.loads(
            (PROJECT_ROOT / "results" / "experiment_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        paths = {artifact["path"] for artifact in manifest["artifacts"]}
        self.assertTrue(
            {
                "data/nsw_dw.dta",
                "results/nsw_experiment_summary.csv",
                "results/nsw_experiment_seed_summary.csv",
                "results/nsw_method_error_records.csv",
                "results/nsw_experiment_metadata.json",
                "results/figures/nsw_experiment_overview.png",
                "results/tables/nsw_experiment_tables.md",
                "docs/stages/nsw_experiment.md",
            }.issubset(paths)
        )
        self.assertEqual(
            manifest["result_row_counts"]["nsw_experiment_summary.csv"],
            5,
        )


if __name__ == "__main__":
    unittest.main()
