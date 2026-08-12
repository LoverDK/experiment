"""End-to-end tests for the paper's Algorithm 1 dispatcher."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path
from statistics import NormalDist
from unittest.mock import patch

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.algorithm1 import (
    Algorithm1Config,
    BridgeCandidate,
    _interval_diameter,
    expected_partial_id_diameter,
    run_algorithm1,
)
from causal_atlas_sim.dgp import (
    AssumptionProfile,
    Mechanism,
    SimulationConfig,
    generate_minimal_archive,
)
from causal_atlas_sim.methods import (
    AtlasConfig,
    compute_certificate,
    design_compatible,
    filter_design_compatible_candidates,
    honest_interval_radius,
    optimize_support_weights,
    retrieve_semantic_candidates,
)
from causal_atlas_sim.partial_identification import PartialIdentificationInterval


class _Unreadable:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError("Algorithm 1 read simulation-only target information.")

    def __float__(self) -> float:
        raise AssertionError("Algorithm 1 read an unobserved bridge outcome.")


def _candidate(generated, key: str, offset: float = 0.0) -> BridgeCandidate:
    representation = np.clip(
        generated.target.observed_representation
        + np.array([offset, 0.0, 0.0, 0.0]),
        -1.0,
        1.0,
    )
    return BridgeCandidate(
        key=key,
        family="test",
        mechanism=Mechanism.from_array(representation),
        observed_representation=representation,
        standard_error=0.10,
        moderator_sensitivity_radius=generated.target.moderator_sensitivity_radius,
        true_effect=generated.target.true_effect,
        observed_effect=generated.target.estimated_effect,
    )


class Algorithm1Tests(unittest.TestCase):
    def test_accepted_branch_returns_only_point_prediction_and_honest_interval(self) -> None:
        generated = generate_minimal_archive(seed=1001)
        result = run_algorithm1(
            generated.archive,
            generated.target,
            (_candidate(generated, "unused"),),
            Algorithm1Config(
                atlas_config=AtlasConfig(scientific_tolerance=100.0),
                bridge_budget=1,
            ),
        )
        self.assertEqual(result.branch, "accepted_composition")
        self.assertIsNotNone(result.atlas_result.point_estimate)
        self.assertIsNone(result.partial_interval)
        self.assertEqual(result.selected_bridge_keys, ())
        self.assertEqual(result.partial_diameter_path, ())

    def test_rejected_branch_builds_partial_id_and_spends_bridge_budget(self) -> None:
        generated = generate_minimal_archive(
            SimulationConfig(target_shift_fraction=0.60),
            seed=1002,
        )
        result = run_algorithm1(
            generated.archive,
            generated.target,
            (_candidate(generated, "exact"),),
            Algorithm1Config(
                atlas_config=AtlasConfig(scientific_tolerance=0.0),
                bridge_budget=1,
            ),
        )
        self.assertEqual(result.branch, "rejected_partial_id")
        self.assertIsNone(result.atlas_result.point_estimate)
        self.assertIsNotNone(result.partial_interval)
        self.assertEqual(result.selected_bridge_keys, ("exact",))
        self.assertEqual(len(result.partial_diameter_path), 2)

    def test_target_truth_and_candidate_oracle_mechanism_are_not_read(self) -> None:
        generated = generate_minimal_archive(seed=1003)
        guarded_target = replace(
            generated.target,
            mechanism=_Unreadable(),
            true_effect=_Unreadable(),
        )
        guarded_candidate = replace(
            _candidate(generated, "guarded"),
            mechanism=_Unreadable(),
            true_effect=_Unreadable(),
        )
        diameter = expected_partial_id_diameter(
            generated.archive,
            guarded_target,
            guarded_candidate,
            AtlasConfig(),
            max_singletons=2,
            quadrature_points=3,
        )
        self.assertTrue(np.isfinite(diameter))

    def test_unselected_candidate_outcome_remains_unread(self) -> None:
        generated = generate_minimal_archive(seed=1004)
        selected = _candidate(generated, "selected")
        guarded = replace(
            _candidate(generated, "guarded", offset=0.8),
            observed_effect=_Unreadable(),
        )

        def fake_expected(archive, target, candidate, config, **kwargs):
            return 1.0 if candidate.key == "selected" else 2.0

        with patch(
            "causal_atlas_sim.algorithm1.expected_partial_id_diameter",
            side_effect=fake_expected,
        ):
            result = run_algorithm1(
                generated.archive,
                generated.target,
                (selected, guarded),
                Algorithm1Config(
                    atlas_config=AtlasConfig(scientific_tolerance=0.0),
                    bridge_budget=1,
                ),
            )
        self.assertEqual(result.selected_bridge_keys, ("selected",))

    def test_each_greedy_step_conditions_on_the_current_selected_set(self) -> None:
        generated = generate_minimal_archive(seed=1005)
        candidates = tuple(
            _candidate(generated, key) for key in ("a", "b", "c")
        )
        calls: list[tuple[tuple[str, ...], str]] = []

        def conditional_expected(archive, target, candidate, config, **kwargs):
            bridge_ids = tuple(
                item.experiment_id
                for item in archive
                if item.experiment_id.startswith("bridge_")
            )
            calls.append((bridge_ids, candidate.key))
            if not bridge_ids:
                return {"a": 1.0, "b": 2.0, "c": 3.0}[candidate.key]
            self.assertEqual(bridge_ids, ("bridge_a",))
            return {"b": 3.0, "c": 2.0}[candidate.key]

        with patch(
            "causal_atlas_sim.algorithm1.expected_partial_id_diameter",
            side_effect=conditional_expected,
        ):
            result = run_algorithm1(
                generated.archive,
                generated.target,
                candidates,
                Algorithm1Config(
                    atlas_config=AtlasConfig(scientific_tolerance=0.0),
                    bridge_budget=2,
                ),
            )
        self.assertEqual(result.selected_bridge_keys, ("a", "c"))
        self.assertIn((("bridge_a",), "b"), calls)
        self.assertIn((("bridge_a",), "c"), calls)

    def test_fixed_seed_reproduces_the_complete_result(self) -> None:
        generated = generate_minimal_archive(seed=1006)
        candidates = tuple(_candidate(generated, key) for key in ("a", "b"))
        config = Algorithm1Config(
            atlas_config=AtlasConfig(scientific_tolerance=0.0),
            bridge_budget=1,
            selection_error_bound=0.01,
        )
        first = run_algorithm1(
            generated.archive,
            generated.target,
            candidates,
            config,
            rng=np.random.default_rng(77),
        )
        second = run_algorithm1(
            generated.archive,
            generated.target,
            candidates,
            config,
            rng=np.random.default_rng(77),
        )
        self.assertEqual(first.selected_bridge_keys, second.selected_bridge_keys)
        self.assertEqual(first.partial_diameter_path, second.partial_diameter_path)

    def test_corollary_5_2_radius_uses_wald_noise_plus_approximation(self) -> None:
        generated = generate_minimal_archive(seed=1007)
        config = AtlasConfig(zeta=0.10)
        candidates = retrieve_semantic_candidates(
            generated.archive,
            generated.target,
            config=config,
        )
        weights, _ = optimize_support_weights(
            generated.archive,
            generated.target,
            candidates,
            config,
        )
        certificate = compute_certificate(
            generated.archive,
            generated.target,
            weights,
            config,
        )
        standard_error = np.sqrt(
            sum(
                weight**2 * item.standard_error_certificate**2
                for weight, item in zip(weights, generated.archive, strict=True)
            )
        )
        expected = (
            certificate.representation_term
            + certificate.curvature_term
            + certificate.hidden_moderator_term
            + certificate.bias_term
            + NormalDist().inv_cdf(0.95) * standard_error
        )
        self.assertAlmostEqual(
            honest_interval_radius(
                generated.archive,
                weights,
                certificate,
                config,
            ),
            expected,
        )

    def test_incompatible_assumption_profile_is_removed(self) -> None:
        generated = generate_minimal_archive(seed=1008)
        incompatible = replace(
            generated.archive[0],
            assumption_profile=AssumptionProfile(
                assignment="nonrandom observational assignment"
            ),
        )
        self.assertFalse(design_compatible(incompatible, generated.target))
        retrieved = retrieve_semantic_candidates(
            (incompatible, *generated.archive[1:]),
            generated.target,
        )
        self.assertIn(0, retrieved)
        candidates = filter_design_compatible_candidates(
            (incompatible, *generated.archive[1:]),
            generated.target,
            retrieved,
        )
        self.assertNotIn(0, candidates)

    def test_empty_partial_id_is_an_inconsistency_not_zero_diameter(self) -> None:
        interval = PartialIdentificationInterval(
            weight_labels=("a",),
            weights=(np.ones(1),),
            centers=(0.0,),
            radii=(1.0,),
            interval_lower=1.0,
            interval_upper=-1.0,
            total_zeta=0.05,
            component_zeta=0.05,
        )
        self.assertTrue(np.isinf(_interval_diameter(interval)))


if __name__ == "__main__":
    unittest.main()
