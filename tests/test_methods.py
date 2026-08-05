"""Tests for transport weights, certificates, rejection, and baselines."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim import generate_minimal_archive
from causal_atlas_sim.methods import (
    AtlasConfig,
    compute_certificate,
    fit_causal_atlas,
    fit_global_mean,
    fit_nearest_semantic_neighbor,
    fit_no_rejection_atlas,
    fit_semantic_forced_composition,
    optimize_support_weights,
    retrieve_semantic_candidates,
)


class MethodTests(unittest.TestCase):
    def setUp(self) -> None:
        generated = generate_minimal_archive(seed=101)
        self.archive = generated.archive
        self.target = generated.target

    def test_candidate_order_is_deterministic_and_design_filtered(self) -> None:
        first = retrieve_semantic_candidates(self.archive, self.target)
        second = retrieve_semantic_candidates(self.archive, self.target)
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(range(len(self.archive))))

    def test_simplex_optimizer_returns_valid_weights(self) -> None:
        candidates = retrieve_semantic_candidates(self.archive, self.target, max_candidates=4)
        weights, objective = optimize_support_weights(
            self.archive, self.target, candidates, AtlasConfig()
        )
        self.assertTrue(np.all(weights >= -1e-12))
        self.assertAlmostEqual(float(weights.sum()), 1.0)
        self.assertGreaterEqual(np.count_nonzero(weights), 1)
        self.assertLessEqual(np.count_nonzero(weights), len(candidates))
        self.assertGreaterEqual(objective, 0.0)

    def test_certificate_decomposes_to_its_declared_terms(self) -> None:
        weights = np.full(len(self.archive), 1.0 / len(self.archive))
        certificate = compute_certificate(self.archive, self.target, weights)
        self.assertAlmostEqual(
            certificate.radius,
            certificate.representation_term
            + certificate.curvature_term
            + certificate.hidden_moderator_term
            + certificate.bias_term
            + certificate.statistical_term,
        )

    def test_rejection_and_no_rejection_share_weights(self) -> None:
        config = AtlasConfig(scientific_tolerance=0.0)
        rejected = fit_causal_atlas(self.archive, self.target, config)
        ablation = fit_no_rejection_atlas(self.archive, self.target, config)
        self.assertFalse(rejected.accepted)
        np.testing.assert_allclose(rejected.weights, ablation.weights)
        self.assertIsNone(rejected.point_estimate)
        self.assertIsNotNone(ablation.point_estimate)

    def test_baselines_produce_finite_point_estimates(self) -> None:
        for estimator in (
            fit_semantic_forced_composition,
            fit_nearest_semantic_neighbor,
            fit_global_mean,
        ):
            result = estimator(self.archive, self.target)
            self.assertTrue(result.accepted)
            self.assertTrue(np.isfinite(result.point_estimate))
            self.assertAlmostEqual(float(result.weights.sum()), 1.0)


if __name__ == "__main__":
    unittest.main()
