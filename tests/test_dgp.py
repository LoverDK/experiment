"""Tests for the certified minimal synthetic data generator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim import (
    EFFECT_CURVATURE_BOUND,
    EFFECT_LIPSCHITZ_BOUND,
    effect_gradient,
    effect_hessian,
    generate_minimal_archive,
    minimal_assumption_report,
    SimulationConfig,
)


class MinimalDGPTests(unittest.TestCase):
    def setUp(self) -> None:
        self.generated = generate_minimal_archive(seed=91)

    def test_all_five_assumption_certificates_hold(self) -> None:
        report = minimal_assumption_report(self.generated)
        self.assertTrue(all(certificate["satisfied"] for certificate in report.values()))

    def test_target_has_exact_oracle_causal_support(self) -> None:
        self.assertLessEqual(self.generated.support_residual(), 1e-12)

    def test_observed_outcomes_satisfy_consistency(self) -> None:
        for experiment in (*self.generated.archive, self.generated.target):
            expected = np.where(
                experiment.treatment == 1,
                experiment.potential_outcome_treated,
                experiment.potential_outcome_control,
            )
            np.testing.assert_array_equal(experiment.observed_outcome, expected)

    def test_aipw_certificate_matches_its_declared_variance_proxy(self) -> None:
        for experiment in (*self.generated.archive, self.generated.target):
            self.assertAlmostEqual(
                experiment.standard_error_certificate**2,
                experiment.variance_proxy / experiment.n_units,
            )
            self.assertAlmostEqual(experiment.nuisance_bias_bound, 0.0)

    def test_smoothness_bounds_hold_on_random_points_in_mechanism_space(self) -> None:
        rng = np.random.default_rng(7)
        for mechanism in rng.uniform(-1.0, 1.0, size=(500, 4)):
            self.assertLessEqual(np.linalg.norm(effect_gradient(mechanism)), EFFECT_LIPSCHITZ_BOUND)
            self.assertLessEqual(
                np.linalg.norm(effect_hessian(mechanism), ord=2), EFFECT_CURVATURE_BOUND
            )

    def test_moderator_certificate_covers_proxy_composition_gap(self) -> None:
        self.assertLessEqual(
            self.generated.proxy_gap_discrepancy(),
            self.generated.hidden_moderator_certificate(),
        )

    def test_heterogeneous_archive_moderator_radii_remain_certified(self) -> None:
        generated = generate_minimal_archive(
            SimulationConfig(archive_moderator_radius_spread=0.40),
            seed=92,
        )
        radii = [experiment.moderator_sensitivity_radius for experiment in generated.archive]
        self.assertAlmostEqual(min(radii), 0.20)
        self.assertAlmostEqual(max(radii), 0.60)
        self.assertTrue(
            all(item["satisfied"] for item in minimal_assumption_report(generated).values())
        )


if __name__ == "__main__":
    unittest.main()
