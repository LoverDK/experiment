"""Tests for deterministic paper-facing simulation artifacts."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.paper_artifacts import (
    render_paper_results_section,
    render_paper_results_tables,
)
from causal_atlas_sim.reporting import build_artifact_manifest, load_result_bundle


class PaperArtifactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_result_bundle(PROJECT_ROOT / "results")

    def test_section_links_to_the_three_committed_figures(self) -> None:
        section = render_paper_results_section(self.bundle)
        self.assertIn("main_experiment_mae.png", section)
        self.assertIn("formal_experiment_overview.png", section)
        self.assertIn("calibration_experiment_overview.png", section)
        self.assertIn("0.7233", section)
        self.assertIn("7.0760", section)
        self.assertIn("1.8772", section)

    def test_latex_tables_preserve_key_benchmark_and_boundary_values(self) -> None:
        tables = render_paper_results_tables(self.bundle)
        self.assertIn("\\label{tab:causal-atlas-nominal}", tables)
        self.assertIn("\\label{tab:causal-atlas-failure-boundary}", tables)
        self.assertIn("0.1109", tables)
        self.assertIn("0.9933", tables)
        self.assertEqual(tables.count("Causal ATLAS"), 1)

    def test_manifest_includes_the_paper_facing_artifacts(self) -> None:
        paths = {
            artifact["path"]
            for artifact in build_artifact_manifest(PROJECT_ROOT)["artifacts"]
        }
        self.assertIn("docs/paper_results_section.md", paths)
        self.assertIn("results/tables/paper_results_tables.tex", paths)


if __name__ == "__main__":
    unittest.main()
