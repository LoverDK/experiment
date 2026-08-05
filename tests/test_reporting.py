"""Tests for deterministic final reporting and artifact validation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.reporting import (
    build_artifact_manifest,
    load_result_bundle,
    render_final_report,
    render_final_summary_tables,
)


class ReportingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_result_bundle(PROJECT_ROOT / "results")

    def test_committed_result_row_counts_are_valid(self) -> None:
        self.assertEqual(len(self.bundle.main_rows), 60)
        self.assertEqual(len(self.bundle.formal_rows), 42)
        self.assertEqual(len(self.bundle.calibration_rows), 12)

    def test_report_is_derived_from_key_result_values(self) -> None:
        report = render_final_report(self.bundle)
        self.assertIn("0.4567", report)
        self.assertIn("0.1111", report)
        self.assertIn("0.7533", report)
        self.assertIn("Assumption 3.1--3.5", report)

    def test_compact_tables_include_benchmark_and_failure_boundary(self) -> None:
        tables = render_final_summary_tables(self.bundle)
        self.assertIn("Nominal multi-seed benchmark", tables)
        self.assertIn("Failure-boundary comparison", tables)
        self.assertIn("understated_smoothness", tables)

    def test_manifest_hashes_existing_artifacts(self) -> None:
        report_path = PROJECT_ROOT / "docs" / "final_experiment_report.md"
        self.assertTrue(report_path.exists())
        manifest = build_artifact_manifest(PROJECT_ROOT)
        self.assertGreaterEqual(len(manifest["artifacts"]), 10)
        self.assertTrue(
            all(len(artifact["sha256"]) == 64 for artifact in manifest["artifacts"])
        )


if __name__ == "__main__":
    unittest.main()
