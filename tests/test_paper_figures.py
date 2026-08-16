"""Tests for the saved submission-facing figures and their source data."""

from __future__ import annotations

import csv
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results"


class PaperFigureTests(unittest.TestCase):
    def test_submission_figures_exist_in_png_and_pdf(self) -> None:
        stems = (
            "synthetic_composability_overview",
            "selective_uncertainty_overview",
            "rejection_bridge_overview",
            "nsw_diagnostics_overview",
            "legacy_layout_synthetic_validation",
            "legacy_layout_nsw_validation",
        )
        for stem in stems:
            for suffix in (".png", ".pdf"):
                with self.subTest(stem=stem, suffix=suffix):
                    path = RESULTS_DIR / "figures" / f"{stem}{suffix}"
                    self.assertTrue(path.is_file(), path)
                    self.assertGreater(path.stat().st_size, 1_000)

    def test_submission_tables_exist(self) -> None:
        paths = (
            RESULTS_DIR / "tables" / "main_synthetic_table.md",
            RESULTS_DIR / "tables" / "main_synthetic_table.tex",
            RESULTS_DIR / "tables" / "support_failure_table.md",
            RESULTS_DIR / "tables" / "support_failure_table.tex",
            RESULTS_DIR / "tables" / "representation_sensitivity_tables.md",
            RESULTS_DIR / "tables" / "legacy_layout_table1_synthetic.md",
            RESULTS_DIR / "tables" / "legacy_layout_table1_synthetic.tex",
            RESULTS_DIR / "tables" / "legacy_layout_table2_bridge.md",
            RESULTS_DIR / "tables" / "legacy_layout_table2_bridge.tex",
            RESULTS_DIR / "tables" / "legacy_layout_table3_nsw.md",
            RESULTS_DIR / "tables" / "legacy_layout_table3_nsw.tex",
        )
        for path in paths:
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 100)

    def test_new_result_row_counts_match_the_fixed_protocols(self) -> None:
        expected = {
            "representation_sensitivity_summary.csv": 25,
            "certificate_diagnostics_summary.csv": 300,
            "synthetic_benchmark_summary.csv": 6,
            "bridge_budget_path_summary.csv": 15,
            "nsw_diagnostics_summary.csv": 1_680,
            "nsw_archive_map_summary.csv": 112,
            "nsw_method_error_records.csv": 8_400,
        }
        for filename, expected_rows in expected.items():
            with self.subTest(filename=filename):
                with (RESULTS_DIR / filename).open(
                    newline="", encoding="utf-8"
                ) as source:
                    self.assertEqual(sum(1 for _ in csv.DictReader(source)), expected_rows)

    def test_legacy_layout_tables_use_current_protocol_values(self) -> None:
        synthetic = (RESULTS_DIR / "tables" / "legacy_layout_table1_synthetic.md").read_text(
            encoding="utf-8"
        )
        bridge = (RESULTS_DIR / "tables" / "legacy_layout_table2_bridge.md").read_text(
            encoding="utf-8"
        )
        nsw = (RESULTS_DIR / "tables" / "legacy_layout_table3_nsw.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("| Causal ATLAS | 0.463 | 0.111 |", synthetic)
        self.assertIn("| Causal-support greedy | 6.942 | 1.877 | 0.730 |", bridge)
        self.assertIn("| Causal ATLAS | 0.862 | 0.699 |", nsw)

    def test_figure_builder_does_not_generate_simulation_data(self) -> None:
        source = (
            PROJECT_ROOT / "src" / "causal_atlas_sim" / "paper_figures.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("generate_minimal_archive", source)
        self.assertNotIn("from .dgp import", source)


if __name__ == "__main__":
    unittest.main()
