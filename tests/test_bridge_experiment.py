"""Tests for the Theorem 5.6 bridge-design experiment."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.bridge_experiment import (
    BridgeCandidate,
    BridgeExperimentConfig,
    BridgeScenario,
    _build_bridge_library,
    default_bridge_policies,
    run_bridge_experiment,
)
from causal_atlas_sim.dgp import generate_minimal_archive
from causal_atlas_sim.reporting import build_artifact_manifest


class BridgeExperimentTests(unittest.TestCase):
    def test_candidate_library_has_causal_and_semantic_design_families(self) -> None:
        config = BridgeExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(1,),
            scenarios=(BridgeScenario("strong", "strong", 0.60),),
        )
        generated = generate_minimal_archive(
            config.dgp_config,
            seed=501,
        )
        candidates = _build_bridge_library(
            generated.target,
            config,
            np.random.default_rng(502),
        )
        self.assertEqual(len(candidates), 12)
        self.assertEqual(
            {candidate.family for candidate in candidates},
            {"causal_full", "semantic_trap", "mixed"},
        )
        self.assertEqual(
            [policy.planning_dimensions for policy in default_bridge_policies()],
            [(0, 1, 2, 3), (0, 1), None],
        )

    def test_policy_paths_use_the_algorithm1_partial_id_diameter(self) -> None:
        config = BridgeExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(3,),
            scenarios=(BridgeScenario("strong", "strong", 0.60),),
            bridge_budget=1,
        )
        result = run_bridge_experiment(config)
        self.assertEqual(len(result.records), 6)
        self.assertTrue(
            all(len(record.evaluation_diameter_path) == 2 for record in result.records)
        )
        self.assertTrue(
            all(
                np.all(np.isfinite(record.evaluation_diameter_path))
                for record in result.records
            )
        )
        self.assertTrue(all(row.budget_completion_rate == 1.0 for row in result.rows))

    def test_multi_seed_protocol_is_deterministic(self) -> None:
        config = BridgeExperimentConfig(
            repetitions_per_seed=3,
            base_seeds=(31, 32),
            scenarios=(
                BridgeScenario("supported", "supported", 0.0),
                BridgeScenario("strong", "strong", 0.60),
            ),
            bridge_budget=2,
        )
        first = run_bridge_experiment(config)
        second = run_bridge_experiment(config)
        self.assertEqual(len(first.records), 36)
        self.assertEqual(len(first.rows), 6)
        self.assertTrue(all(row.repetitions == 6 for row in first.rows))
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_manifest_includes_stage_eleven_artifacts(self) -> None:
        manifest = build_artifact_manifest(PROJECT_ROOT)
        paths = {artifact["path"] for artifact in manifest["artifacts"]}
        self.assertTrue(
            {
                "results/bridge_experiment_summary.csv",
                "results/bridge_experiment_seed_summary.csv",
                "results/bridge_experiment_metadata.json",
                "results/figures/bridge_experiment_overview.png",
                "results/tables/bridge_experiment_tables.md",
            }.issubset(paths)
        )
        self.assertEqual(
            manifest["result_row_counts"]["bridge_experiment_summary.csv"],
            12,
        )


if __name__ == "__main__":
    unittest.main()
