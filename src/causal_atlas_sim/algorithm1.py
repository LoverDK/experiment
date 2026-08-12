"""End-to-end implementation of paper Algorithm 1.

The entry point first attempts certified composition.  Only a rejected target
is routed to Theorem 5.4 partial identification and greedy bridge design.
Bridge candidates are ranked by conditional marginal expected reduction of
the partial-identification diameter under a declared plug-in design model.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Sequence

import numpy as np

from .dgp import ExperimentData, Mechanism
from .methods import AtlasConfig, AtlasResult, fit_causal_atlas
from .partial_identification import (
    PartialIdentificationInterval,
    construct_partial_identification_interval,
)


@dataclass(frozen=True)
class BridgeCandidate:
    """A proposed bridge design plus simulation-only outcome metadata.

    Selection reads the public representation, design standard error and
    moderator radius.  ``observed_effect`` becomes available only after the
    candidate is selected.  ``mechanism`` and ``true_effect`` are never read by
    Algorithm 1 and are retained solely for synthetic evaluation.
    """

    key: str
    family: str
    mechanism: object
    observed_representation: np.ndarray
    standard_error: float
    moderator_sensitivity_radius: float
    true_effect: float
    observed_effect: float


@dataclass(frozen=True)
class Algorithm1Config:
    """Inputs and numerical controls appearing in Algorithm 1."""

    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    max_singletons: int = 4
    bridge_budget: int = 0
    bridge_quadrature_points: int = 3
    planning_dimensions: tuple[int, ...] = (0, 1, 2, 3)
    selection_mode: str = "voi"
    selection_error_bound: float = 0.0
    planning_max_iterations: int = 80

    def __post_init__(self) -> None:
        if self.max_singletons < 1:
            raise ValueError("max_singletons must be positive.")
        if self.bridge_budget < 0:
            raise ValueError("bridge_budget must be nonnegative.")
        if self.bridge_quadrature_points < 1:
            raise ValueError("bridge_quadrature_points must be positive.")
        if not self.planning_dimensions:
            raise ValueError("planning_dimensions cannot be empty.")
        if self.selection_mode not in {"voi", "random"}:
            raise ValueError("selection_mode must be 'voi' or 'random'.")
        if self.selection_error_bound < 0.0:
            raise ValueError("selection_error_bound must be nonnegative.")
        if self.planning_max_iterations < 1:
            raise ValueError("planning_max_iterations must be positive.")


@dataclass(frozen=True)
class Algorithm1Result:
    """Certified output from the accepted or rejected branch of Algorithm 1."""

    atlas_result: AtlasResult
    partial_interval: PartialIdentificationInterval | None
    updated_partial_interval: PartialIdentificationInterval | None
    selected_bridge_keys: tuple[str, ...]
    selected_bridge_families: tuple[str, ...]
    selected_bridge_marginal_values: tuple[float, ...]
    partial_diameter_path: tuple[float, ...]
    planning_diameter_path: tuple[float, ...]
    mean_selection_error: float | None
    stopping_reason: str | None

    @property
    def branch(self) -> str:
        return "accepted_composition" if self.atlas_result.accepted else "rejected_partial_id"


def run_algorithm1(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    bridge_library: Sequence[BridgeCandidate] = (),
    config: Algorithm1Config | None = None,
    *,
    rng: np.random.Generator | None = None,
) -> Algorithm1Result:
    """Run Algorithm 1 in its operational order without target-truth access."""

    config = config or Algorithm1Config()
    rng = rng or np.random.default_rng(0)
    atlas_result = fit_causal_atlas(archive, target, config.atlas_config)
    if atlas_result.accepted:
        return Algorithm1Result(
            atlas_result=atlas_result,
            partial_interval=None,
            updated_partial_interval=None,
            selected_bridge_keys=(),
            selected_bridge_families=(),
            selected_bridge_marginal_values=(),
            partial_diameter_path=(),
            planning_diameter_path=(),
            mean_selection_error=None,
            stopping_reason=None,
        )

    partial_interval = construct_partial_identification_interval(
        archive,
        target,
        config.atlas_config,
        max_singletons=config.max_singletons,
    )
    sources = list(archive)
    remaining = list(bridge_library)
    selected: list[BridgeCandidate] = []
    selected_marginals: list[float] = []
    selection_errors: list[float] = []
    stopping_reason: str | None = None
    evaluation_path = [_interval_diameter(partial_interval)]
    planning_config = replace(
        config.atlas_config,
        representation_dimensions=config.planning_dimensions,
        max_iterations=min(
            config.atlas_config.max_iterations,
            config.planning_max_iterations,
        ),
    )
    planning_interval = construct_partial_identification_interval(
        sources,
        target,
        planning_config,
        max_singletons=config.max_singletons,
    )
    planning_path = [_interval_diameter(planning_interval)]

    steps = min(config.bridge_budget, len(remaining))
    for _ in range(steps):
        current_planning_diameter = _interval_diameter(planning_interval)
        if not np.isfinite(current_planning_diameter):
            # Lemma 5.1 identifies an empty intersection as mutually
            # inconsistent evidence, for which a diameter-based VoI is not
            # defined.  Preserve that diagnostic rather than rewarding it as
            # a zero-width set.
            stopping_reason = "current_partial_id_certificates_inconsistent"
            break
        if config.selection_mode == "random":
            chosen_index = int(rng.integers(len(remaining)))
            chosen_marginal = float("nan")
        else:
            scores: list[tuple[float, int, float, float]] = []
            for index, candidate in enumerate(remaining):
                expected_diameter = expected_partial_id_diameter(
                    sources,
                    target,
                    candidate,
                    planning_config,
                    max_singletons=config.max_singletons,
                    quadrature_points=config.bridge_quadrature_points,
                )
                marginal = current_planning_diameter - expected_diameter
                error = rng.uniform(
                    -config.selection_error_bound,
                    config.selection_error_bound,
                )
                scores.append((marginal + error, -index, marginal, abs(error)))
            feasible_scores = [score for score in scores if np.isfinite(score[0])]
            if not feasible_scores:
                stopping_reason = "no_candidate_has_finite_expected_diameter"
                break
            _, negative_index, chosen_marginal, absolute_error = max(feasible_scores)
            chosen_index = -negative_index
            selection_errors.append(absolute_error)

        chosen = remaining.pop(chosen_index)
        selected.append(chosen)
        selected_marginals.append(chosen_marginal)
        sources.append(_candidate_experiment(chosen, target, chosen.observed_effect))

        planning_interval = construct_partial_identification_interval(
            sources,
            target,
            planning_config,
            max_singletons=config.max_singletons,
        )
        planning_path.append(_interval_diameter(planning_interval))
        evaluation_interval = construct_partial_identification_interval(
            sources,
            target,
            config.atlas_config,
            max_singletons=config.max_singletons,
        )
        evaluation_path.append(_interval_diameter(evaluation_interval))

    if stopping_reason is None and not np.isfinite(planning_path[-1]):
        stopping_reason = "final_planning_certificates_inconsistent"

    updated = (
        construct_partial_identification_interval(
            sources,
            target,
            config.atlas_config,
            max_singletons=config.max_singletons,
        )
        if selected
        else partial_interval
    )
    return Algorithm1Result(
        atlas_result=atlas_result,
        partial_interval=partial_interval,
        updated_partial_interval=updated,
        selected_bridge_keys=tuple(candidate.key for candidate in selected),
        selected_bridge_families=tuple(candidate.family for candidate in selected),
        selected_bridge_marginal_values=tuple(selected_marginals),
        partial_diameter_path=tuple(evaluation_path),
        planning_diameter_path=tuple(planning_path),
        mean_selection_error=(
            float(np.mean(selection_errors)) if selection_errors else None
        ),
        stopping_reason=stopping_reason,
    )


def expected_partial_id_diameter(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    candidate: BridgeCandidate,
    config: AtlasConfig,
    *,
    max_singletons: int,
    quadrature_points: int,
) -> float:
    """Estimate E_b[diameter] under a plug-in normal bridge design model."""

    candidate_target = _candidate_experiment(candidate, target, 0.0)
    predictive_fit = fit_causal_atlas(archive, candidate_target, config)
    predictive_mean = predictive_fit.raw_point_estimate
    if predictive_mean is None:
        predictive_mean = float(
            np.mean([experiment.estimated_effect for experiment in archive])
        )
    nodes, weights = np.polynomial.hermite.hermgauss(quadrature_points)
    total = 0.0
    for node, quadrature_weight in zip(nodes, weights, strict=True):
        hypothetical_effect = float(
            predictive_mean + np.sqrt(2.0) * candidate.standard_error * node
        )
        augmented = (
            *archive,
            _candidate_experiment(candidate, target, hypothetical_effect),
        )
        interval = construct_partial_identification_interval(
            augmented,
            target,
            config,
            max_singletons=max_singletons,
        )
        total += float(quadrature_weight) * _interval_diameter(interval)
    return float(total / np.sqrt(np.pi))


def _candidate_experiment(
    candidate: BridgeCandidate,
    target: ExperimentData,
    estimated_effect: float,
) -> ExperimentData:
    """Encode a proposed or observed bridge as a certified archive object."""

    empty_vector = np.empty(0, dtype=float)
    observed_representation = np.asarray(
        candidate.observed_representation,
        dtype=float,
    ).copy()
    return ExperimentData(
        experiment_id=f"bridge_{candidate.key}",
        # The ExperimentData schema carries an oracle mechanism for synthetic
        # evaluation.  Algorithm 1 must not inspect it, so the planning object
        # receives a placeholder reconstructed only from public coordinates.
        mechanism=Mechanism.from_array(observed_representation),
        observed_representation=observed_representation,
        design=target.design,
        assumption_profile=target.assumption_profile,
        x=np.empty((0, target.x.shape[1]), dtype=float),
        treatment=np.empty(0, dtype=np.int8),
        observed_outcome=empty_vector,
        potential_outcome_control=empty_vector,
        potential_outcome_treated=empty_vector,
        aipw_scores=empty_vector,
        true_effect=float("nan"),
        estimated_effect=float(estimated_effect),
        variance_proxy=float(candidate.standard_error**2),
        standard_error_certificate=float(candidate.standard_error),
        nuisance_bias_bound=0.0,
        known_propensity=target.known_propensity,
        moderator_sensitivity_radius=float(
            candidate.moderator_sensitivity_radius
        ),
    )


def _interval_diameter(interval: PartialIdentificationInterval) -> float:
    """Return the interval diameter or infinity for inconsistent certificates."""

    return float(interval.width) if interval.width is not None else float("inf")
