"""Tests for oracle evaluation and target-level certificate diagnostics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim import generate_minimal_archive
from causal_atlas_sim.certificate_diagnostics import (
    BENCHMARK_METHODS,
    CertificateDiagnosticsConfig,
    run_certificate_diagnostics,
)
from causal_atlas_sim.evaluation_baselines import fit_oracle_latent_support


class CertificateDiagnosticsTests(unittest.TestCase):
    def test_oracle_is_explicit_and_does_not_mutate_public_inputs(self) -> None:
        generated = generate_minimal_archive(seed=811)
        public_target = generated.target.observed_representation.copy()
        public_archive = [item.observed_representation.copy() for item in generated.archive]
        result = fit_oracle_latent_support(generated.archive, generated.target)
        self.assertEqual(result.method, "oracle_latent_support")
        self.assertTrue(result.accepted)
        np.testing.assert_array_equal(generated.target.observed_representation, public_target)
        for experiment, expected in zip(generated.archive, public_archive, strict=True):
            np.testing.assert_array_equal(experiment.observed_representation, expected)

    def test_diagnostics_emit_target_records_and_six_method_table(self) -> None:
        config = CertificateDiagnosticsConfig(
            repetitions_per_seed=2,
            base_seeds=(812,),
        )
        result = run_certificate_diagnostics(config)
        self.assertEqual(len(result.records), 2)
        self.assertEqual(
            {row.method for row in result.benchmark_rows},
            set(BENCHMARK_METHODS),
        )
        self.assertTrue(
            all(
                np.isclose(
                    record.certificate_radius,
                    record.representation_term
                    + record.curvature_term
                    + record.hidden_moderator_term
                    + record.bias_term
                    + record.statistical_term,
                )
                for record in result.records
            )
        )
        self.assertIn("oracle_scope", result.to_dict())


if __name__ == "__main__":
    unittest.main()
