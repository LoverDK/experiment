"""Causal ATLAS transport and transparent comparison baselines.

The estimators in this module only consume the information an applied method
would receive: observed representations, design profiles, effect estimates,
and uncertainty certificates.  True mechanisms and true effects remain in
the DGP object solely for evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf, log, sqrt
from statistics import NormalDist
from typing import Sequence

import numpy as np

from .dgp import (
    EFFECT_CURVATURE_BOUND,
    EFFECT_LIPSCHITZ_BOUND,
    HIDDEN_MODERATOR_LIPSCHITZ_BOUND,
    ExperimentData,
)


@dataclass(frozen=True)
class AtlasConfig:
    """Tuning and certification constants for the transport estimators."""

    max_candidates: int | None = None
    semantic_radius: float | None = None
    representation_dimensions: tuple[int, ...] | None = None
    lambda_sigma: float = 1.0
    lambda_hidden: float = 1.0
    effect_lipschitz_bound: float = EFFECT_LIPSCHITZ_BOUND
    effect_curvature_bound: float = EFFECT_CURVATURE_BOUND
    hidden_moderator_lipschitz_bound: float = HIDDEN_MODERATOR_LIPSCHITZ_BOUND
    zeta: float = 0.05
    # This illustrative threshold intentionally yields both accepted and
    # rejected draws; users should set it from their scientific decision rule.
    scientific_tolerance: float = 1.65
    max_iterations: int = 800
    learning_rate: float = 0.25
    convergence_tolerance: float = 1e-10

    def __post_init__(self) -> None:
        if self.max_candidates is not None and self.max_candidates < 1:
            raise ValueError("max_candidates must be positive when supplied.")
        if self.semantic_radius is not None and self.semantic_radius < 0.0:
            raise ValueError("semantic_radius must be nonnegative.")
        if self.representation_dimensions is not None:
            if not self.representation_dimensions:
                raise ValueError("representation_dimensions cannot be empty.")
            if len(set(self.representation_dimensions)) != len(self.representation_dimensions):
                raise ValueError("representation_dimensions cannot contain duplicates.")
            if min(self.representation_dimensions) < 0 or max(self.representation_dimensions) > 3:
                raise ValueError("representation_dimensions must index the four-coordinate representation.")
        if self.lambda_sigma < 0.0 or self.lambda_hidden < 0.0:
            raise ValueError("regularization strengths must be nonnegative.")
        if self.effect_lipschitz_bound <= 0.0 or self.effect_curvature_bound <= 0.0:
            raise ValueError("smoothness bounds must be positive.")
        if self.hidden_moderator_lipschitz_bound < 0.0:
            raise ValueError("hidden moderator bound must be nonnegative.")
        if not 0.0 < self.zeta < 1.0:
            raise ValueError("zeta must lie in (0, 1).")
        if self.scientific_tolerance < 0.0:
            raise ValueError("scientific_tolerance must be nonnegative.")
        if self.max_iterations < 1 or self.learning_rate <= 0.0:
            raise ValueError("optimization controls must be positive.")


@dataclass(frozen=True)
class Certificate:
    """Decomposed finite-sample transport certificate."""

    radius: float
    representation_term: float
    curvature_term: float
    hidden_moderator_term: float
    bias_term: float
    statistical_term: float

    @property
    def interval_half_width(self) -> float:
        return self.radius


@dataclass(frozen=True)
class AtlasResult:
    """One method's prediction and certificate for one held-out target."""

    method: str
    candidate_indices: tuple[int, ...]
    candidate_distances: tuple[float, ...]
    weights: np.ndarray
    raw_point_estimate: float | None
    point_estimate: float | None
    accepted: bool
    rejection_reason: str | None
    certificate: Certificate
    interval_lower: float
    interval_upper: float
    objective_value: float | None

    @property
    def rejected(self) -> bool:
        return not self.accepted

    @property
    def interval(self) -> tuple[float, float]:
        return (self.interval_lower, self.interval_upper)


def design_compatible(source: ExperimentData, target: ExperimentData) -> bool:
    """Apply the recorded design and estimand compatibility filter."""

    return bool(
        source.design == target.design
        and source.assumption_profile == target.assumption_profile
    )


def _observed_representation(
    experiment: ExperimentData,
    config: AtlasConfig,
) -> np.ndarray:
    """Return the prespecified representation coordinates used by one policy."""

    values = np.asarray(experiment.observed_representation, dtype=float)
    if config.representation_dimensions is None:
        return values
    return values[list(config.representation_dimensions)]


def retrieve_semantic_candidates(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    *,
    max_candidates: int | None = None,
    semantic_radius: float | None = None,
    config: AtlasConfig | None = None,
) -> tuple[int, ...]:
    """Algorithm 1 line 2: retrieve by public representation and metadata."""

    config = config or AtlasConfig(
        max_candidates=max_candidates,
        semantic_radius=semantic_radius,
    )
    target_representation = _observed_representation(target, config)
    scored = [
        (
            float(
                np.linalg.norm(
                    _observed_representation(source, config) - target_representation
                )
            ),
            index,
        )
        for index, source in enumerate(archive)
    ]
    scored.sort(key=lambda item: (item[0], item[1]))
    if config.semantic_radius is not None:
        scored = [item for item in scored if item[0] <= config.semantic_radius + 1e-12]
    if config.max_candidates is not None:
        scored = scored[: config.max_candidates]
    return tuple(index for _, index in scored)


def filter_design_compatible_candidates(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    candidate_indices: Sequence[int],
) -> tuple[int, ...]:
    """Algorithm 1 line 3: remove candidates failing kappa(source, target)."""

    return tuple(
        index
        for index in candidate_indices
        if design_compatible(archive[index], target)
    )


def _project_to_simplex(values: np.ndarray) -> np.ndarray:
    """Euclidean projection onto {w >= 0, sum(w) = 1}."""

    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Simplex projection expects a nonempty vector.")
    sorted_values = np.sort(values)[::-1]
    cumulative = np.cumsum(sorted_values)
    eligible = sorted_values - (cumulative - 1.0) / (np.arange(values.size) + 1) > 0
    if not np.any(eligible):
        return np.full(values.size, 1.0 / values.size)
    rho = int(np.flatnonzero(eligible)[-1])
    threshold = (cumulative[rho] - 1.0) / (rho + 1)
    return np.maximum(values - threshold, 0.0)


def optimize_support_weights(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    candidate_indices: Sequence[int],
    config: AtlasConfig | None = None,
) -> tuple[np.ndarray, float]:
    """Solve the regularized support program on a candidate simplex."""

    config = config or AtlasConfig()
    indices = tuple(candidate_indices)
    if not indices:
        raise ValueError("At least one candidate is required.")
    representations = np.vstack(
        [_observed_representation(archive[index], config) for index in indices]
    )
    target_representation = _observed_representation(target, config)
    standard_error_squares = np.array(
        [archive[index].standard_error_certificate**2 for index in indices], dtype=float
    )
    hidden_radii = np.array(
        [archive[index].moderator_sensitivity_radius for index in indices], dtype=float
    )
    # The hidden target radius is constant in alpha; the archive contribution
    # is linear, so it enters the gradient as a fixed vector.
    hidden_gradient = (
        config.lambda_hidden
        * config.hidden_moderator_lipschitz_bound
        * hidden_radii
    )

    def objective(weights: np.ndarray) -> float:
        residual = target_representation - weights @ representations
        return float(
            residual @ residual
            + config.lambda_sigma * np.sum(weights**2 * standard_error_squares)
            + hidden_gradient @ weights
        )

    def gradient(weights: np.ndarray) -> np.ndarray:
        residual = weights @ representations - target_representation
        return (
            2.0 * representations @ residual
            + 2.0 * config.lambda_sigma * weights * standard_error_squares
            + hidden_gradient
        )

    weights = np.full(len(indices), 1.0 / len(indices))
    step = config.learning_rate
    current = objective(weights)
    for _ in range(config.max_iterations):
        proposal = _project_to_simplex(weights - step * gradient(weights))
        proposed_value = objective(proposal)
        if proposed_value <= current + 1e-14:
            change = float(np.linalg.norm(proposal - weights))
            weights, current = proposal, proposed_value
            step = min(step * 1.05, 1.0)
            if change <= config.convergence_tolerance:
                break
        else:
            step *= 0.5
            if step < 1e-12:
                break
    full_weights = np.zeros(len(archive), dtype=float)
    full_weights[list(indices)] = weights
    return full_weights, float(current)


def compute_certificate(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    weights: np.ndarray,
    config: AtlasConfig | None = None,
) -> Certificate:
    """Compute the observable, curvature, hidden, bias, and statistical terms."""

    config = config or AtlasConfig()
    weights = np.asarray(weights, dtype=float)
    if weights.shape != (len(archive),) or np.any(weights < -1e-10):
        raise ValueError("weights must have one nonnegative entry per archive experiment.")
    if not np.isclose(weights.sum(), 1.0):
        raise ValueError("weights must sum to one.")
    representations = np.vstack(
        [_observed_representation(experiment, config) for experiment in archive]
    )
    weighted_representation = weights @ representations
    representation_term = float(
        config.effect_lipschitz_bound
        * np.linalg.norm(
            _observed_representation(target, config) - weighted_representation
        )
    )
    dispersion = float(
        sum(
            weight
            * np.linalg.norm(
                _observed_representation(experiment, config)
                - weighted_representation
            )
            ** 2
            for weight, experiment in zip(weights, archive, strict=True)
        )
    )
    curvature_term = float(config.effect_curvature_bound * dispersion / 2.0)
    archive_radii = np.array(
        [experiment.moderator_sensitivity_radius for experiment in archive], dtype=float
    )
    hidden_moderator_term = float(
        config.hidden_moderator_lipschitz_bound
        * (target.moderator_sensitivity_radius + weights @ archive_radii)
    )
    bias_term = float(
        sum(weight * experiment.nuisance_bias_bound for weight, experiment in zip(weights, archive, strict=True))
    )
    statistical_term = float(
        sqrt(
            2.0
            * log(2.0 / config.zeta)
            * sum(
                weight**2 * experiment.standard_error_certificate**2
                for weight, experiment in zip(weights, archive, strict=True)
            )
        )
    )
    return Certificate(
        radius=representation_term
        + curvature_term
        + hidden_moderator_term
        + bias_term
        + statistical_term,
        representation_term=representation_term,
        curvature_term=curvature_term,
        hidden_moderator_term=hidden_moderator_term,
        bias_term=bias_term,
        statistical_term=statistical_term,
    )


def honest_interval_radius(
    archive: Sequence[ExperimentData],
    weights: np.ndarray,
    certificate: Certificate,
    config: AtlasConfig | None = None,
) -> float:
    """Return the Corollary 5.2 radius: approximation bound plus Wald noise."""

    config = config or AtlasConfig()
    standard_error = sqrt(
        sum(
            weight**2 * experiment.standard_error_certificate**2
            for weight, experiment in zip(weights, archive, strict=True)
        )
    )
    approximation_radius = (
        certificate.representation_term
        + certificate.curvature_term
        + certificate.hidden_moderator_term
        + certificate.bias_term
    )
    z_value = NormalDist().inv_cdf(1.0 - config.zeta / 2.0)
    return float(approximation_radius + z_value * standard_error)


def fit_causal_atlas(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Fit rejectable Causal ATLAS transport for one target experiment."""

    config = config or AtlasConfig()
    retrieved = retrieve_semantic_candidates(archive, target, config=config)
    candidates = filter_design_compatible_candidates(
        archive, target, retrieved
    )
    if not candidates:
        empty = Certificate(inf, inf, inf, inf, inf, inf)
        return AtlasResult(
            method="atlas",
            candidate_indices=(),
            candidate_distances=(),
            weights=np.zeros(len(archive), dtype=float),
            raw_point_estimate=None,
            point_estimate=None,
            accepted=False,
            rejection_reason="no design-compatible semantic candidates",
            certificate=empty,
            interval_lower=float("nan"),
            interval_upper=float("nan"),
            objective_value=None,
        )
    weights, objective_value = optimize_support_weights(archive, target, candidates, config)
    certificate = compute_certificate(archive, target, weights, config)
    raw = float(sum(weight * experiment.estimated_effect for weight, experiment in zip(weights, archive, strict=True)))
    accepted = bool(certificate.radius <= config.scientific_tolerance + 1e-12)
    distances = tuple(
        float(
            np.linalg.norm(
                _observed_representation(archive[index], config)
                - _observed_representation(target, config)
            )
        )
        for index in candidates
    )
    interval_radius = honest_interval_radius(archive, weights, certificate, config)
    return AtlasResult(
        method="atlas",
        candidate_indices=candidates,
        candidate_distances=distances,
        weights=weights,
        raw_point_estimate=raw,
        point_estimate=raw if accepted else None,
        accepted=accepted,
        rejection_reason=None if accepted else "certificate exceeds scientific tolerance",
        certificate=certificate,
        interval_lower=raw - interval_radius,
        interval_upper=raw + interval_radius,
        objective_value=objective_value,
    )


def fit_no_rejection_atlas(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Ablation using the same learned weights and certificate, but no rejection."""

    result = fit_causal_atlas(archive, target, config)
    return AtlasResult(
        method="atlas_no_rejection",
        candidate_indices=result.candidate_indices,
        candidate_distances=result.candidate_distances,
        weights=result.weights,
        raw_point_estimate=result.raw_point_estimate,
        point_estimate=result.raw_point_estimate,
        accepted=result.raw_point_estimate is not None,
        rejection_reason=None,
        certificate=result.certificate,
        interval_lower=result.interval_lower,
        interval_upper=result.interval_upper,
        objective_value=result.objective_value,
    )


def _uniform_result(
    method: str,
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    indices: Sequence[int],
    config: AtlasConfig,
) -> AtlasResult:
    if not indices:
        raise ValueError("Baseline requires at least one design-compatible archive experiment.")
    weights = np.zeros(len(archive), dtype=float)
    weights[list(indices)] = 1.0 / len(indices)
    return _result_from_weights(method, archive, target, indices, weights, config)


def _result_from_weights(
    method: str,
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    indices: Sequence[int],
    weights: np.ndarray,
    config: AtlasConfig,
) -> AtlasResult:
    certificate = compute_certificate(archive, target, weights, config)
    raw = float(sum(weight * experiment.estimated_effect for weight, experiment in zip(weights, archive, strict=True)))
    distances = tuple(
        float(
            np.linalg.norm(
                _observed_representation(archive[index], config)
                - _observed_representation(target, config)
            )
        )
        for index in indices
    )
    interval_radius = honest_interval_radius(archive, weights, certificate, config)
    return AtlasResult(
        method=method,
        candidate_indices=tuple(indices),
        candidate_distances=distances,
        weights=weights,
        raw_point_estimate=raw,
        point_estimate=raw,
        accepted=True,
        rejection_reason=None,
        certificate=certificate,
        interval_lower=raw - interval_radius,
        interval_upper=raw + interval_radius,
        objective_value=None,
    )


def fit_semantic_forced_composition(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Force a semantic composition using inverse-distance similarity weights."""

    config = config or AtlasConfig()
    indices = filter_design_compatible_candidates(
        archive,
        target,
        retrieve_semantic_candidates(archive, target, config=config),
    )
    if not indices:
        indices = tuple(
            index for index, source in enumerate(archive) if design_compatible(source, target)
        )
    distances = np.array(
        [
            np.linalg.norm(
                _observed_representation(archive[index], config)
                - _observed_representation(target, config)
            )
            for index in indices
        ],
        dtype=float,
    )
    similarities = 1.0 / np.maximum(distances, 1e-8)
    weights = np.zeros(len(archive), dtype=float)
    weights[list(indices)] = similarities / similarities.sum()
    return _result_from_weights("semantic_forced", archive, target, indices, weights, config)


def fit_nearest_semantic_neighbor(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Use the single closest design-compatible semantic neighbor."""

    config = config or AtlasConfig()
    indices = filter_design_compatible_candidates(
        archive,
        target,
        retrieve_semantic_candidates(archive, target, config=config),
    )
    if not indices:
        raise ValueError("No design-compatible semantic neighbor exists.")
    return _uniform_result("nearest_semantic", archive, target, indices[:1], config)


def fit_global_mean(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Use the mean effect estimate over all design-compatible archive studies."""

    config = config or AtlasConfig()
    indices = tuple(
        index for index, source in enumerate(archive) if design_compatible(source, target)
    )
    return _uniform_result("global_mean", archive, target, indices, config)


METHODS = (
    "atlas",
    "atlas_no_rejection",
    "semantic_forced",
    "nearest_semantic",
    "global_mean",
)


def fit_method(
    method: str,
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Dispatch one named estimator."""

    if method == "atlas":
        from .algorithm1 import Algorithm1Config, run_algorithm1

        atlas_config = config or AtlasConfig()
        return run_algorithm1(
            archive,
            target,
            config=Algorithm1Config(atlas_config=atlas_config),
        ).atlas_result
    if method == "atlas_no_rejection":
        return fit_no_rejection_atlas(archive, target, config)
    if method == "semantic_forced":
        return fit_semantic_forced_composition(archive, target, config)
    if method == "nearest_semantic":
        return fit_nearest_semantic_neighbor(archive, target, config)
    if method == "global_mean":
        return fit_global_mean(archive, target, config)
    raise ValueError(f"Unknown method: {method}")
