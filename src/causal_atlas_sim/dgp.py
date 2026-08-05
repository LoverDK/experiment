"""Minimal synthetic archive satisfying Assumptions 3.1--3.5 by construction.

The generator deliberately mirrors the paper's synthetic mechanism:

    m = (s1, s2, h, q)

where h is latent and only a bounded-noise proxy is released.  The target is
constructed as a convex combination of archive mechanisms.  This is a sanity
check setting: it supplies exact causal support while retaining unit-level
randomization, uncertainty certificates, and a nonzero moderator certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np


MECHANISM_LOWER_BOUND = -1.0
MECHANISM_UPPER_BOUND = 1.0

# Conservative analytic bounds on M = [-1, 1]^4 for the paper's effect surface.
EFFECT_LIPSCHITZ_BOUND = 2.61
EFFECT_CURVATURE_BOUND = 1.80
HIDDEN_MODERATOR_LIPSCHITZ_BOUND = 1.55


@dataclass(frozen=True)
class Mechanism:
    """The true, four-dimensional causal mechanism of one experiment."""

    s1: float
    s2: float
    h: float
    q: float

    def as_array(self) -> np.ndarray:
        return np.array([self.s1, self.s2, self.h, self.q], dtype=float)

    @classmethod
    def from_array(cls, value: np.ndarray) -> "Mechanism":
        value = np.asarray(value, dtype=float)
        if value.shape != (4,):
            raise ValueError("A mechanism must have exactly four coordinates.")
        return cls(*map(float, value))


@dataclass(frozen=True)
class DesignProfile:
    """Recorded estimand card used to enforce Assumption 3.2."""

    treatment_contrast: str = "standardized treatment v1 versus no treatment"
    control_condition: str = "no treatment"
    outcome_scale: str = "standardized continuous outcome difference"
    outcome_time_window: str = "one fixed post-treatment period"
    exposure_mapping: str = "individual treatment with no interference"
    sampling_frame: str = "iid draws from one normalized synthetic population"
    estimand: str = "ATE = E[Y(1) - Y(0)]"
    normalization: str = "identity; all effects already share one causal scale"


COMMON_DESIGN = DesignProfile()


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for the first, fully certified synthetic archive."""

    n_archive: int = 8
    n_units_per_experiment: int = 400
    n_units_target: int = 400
    propensity: float = 0.5
    overlap_lower_bound: float = 0.10
    outcome_noise_sd: float = 1.0
    moderator_sensitivity_radius: float = 0.20
    moderator_proxy_half_width: float = 0.10
    target_shift_fraction: float = 0.0
    target_shift_anchor: tuple[float, float, float, float] = (1.0, -1.0, 1.0, -1.0)

    def __post_init__(self) -> None:
        if self.n_archive < 2:
            raise ValueError("At least two archive experiments are required.")
        if self.n_units_per_experiment < 20 or self.n_units_target < 20:
            raise ValueError("Each synthetic experiment needs at least 20 units.")
        if not 0.0 < self.overlap_lower_bound < 0.5:
            raise ValueError("overlap_lower_bound must lie in (0, 0.5).")
        if not self.overlap_lower_bound <= self.propensity <= 1.0 - self.overlap_lower_bound:
            raise ValueError("propensity must satisfy the declared overlap bound.")
        if self.outcome_noise_sd <= 0.0:
            raise ValueError("outcome_noise_sd must be positive.")
        if self.moderator_sensitivity_radius < 0.0:
            raise ValueError("moderator_sensitivity_radius must be nonnegative.")
        if self.moderator_proxy_half_width < 0.0:
            raise ValueError("moderator_proxy_half_width must be nonnegative.")
        if 2.0 * self.moderator_proxy_half_width > self.moderator_sensitivity_radius:
            raise ValueError(
                "The sensitivity radius must cover the diameter of the proxy-compatible h set."
            )
        if not 0.0 <= self.target_shift_fraction <= 1.0:
            raise ValueError("target_shift_fraction must lie in [0, 1].")
        if len(self.target_shift_anchor) != 4 or not all(
            MECHANISM_LOWER_BOUND <= value <= MECHANISM_UPPER_BOUND
            for value in self.target_shift_anchor
        ):
            raise ValueError("target_shift_anchor must be a four-vector in [-1, 1].")


@dataclass(frozen=True)
class ExperimentData:
    """One causally encoded experiment, including synthetic unit records."""

    experiment_id: str
    mechanism: Mechanism
    observed_representation: np.ndarray
    design: DesignProfile
    x: np.ndarray
    treatment: np.ndarray
    observed_outcome: np.ndarray
    potential_outcome_control: np.ndarray
    potential_outcome_treated: np.ndarray
    aipw_scores: np.ndarray
    true_effect: float
    estimated_effect: float
    variance_proxy: float
    standard_error_certificate: float
    nuisance_bias_bound: float
    known_propensity: float
    moderator_sensitivity_radius: float

    @property
    def n_units(self) -> int:
        return int(self.treatment.shape[0])

    @property
    def noise_realization(self) -> float:
        """The realized xi_i in hat(tau)_i = tau_i + xi_i + b_i."""

        return self.estimated_effect - self.true_effect


@dataclass(frozen=True)
class GeneratedArchive:
    """An archive, a held-out target, and oracle-only construction metadata."""

    archive: tuple[ExperimentData, ...]
    target: ExperimentData
    target_support_weights: np.ndarray
    config: SimulationConfig

    def weighted_archive_mechanism(self) -> np.ndarray:
        archive_matrix = np.vstack([experiment.mechanism.as_array() for experiment in self.archive])
        return self.target_support_weights @ archive_matrix

    def support_residual(self) -> float:
        return float(np.linalg.norm(self.target.mechanism.as_array() - self.weighted_archive_mechanism()))

    def hidden_moderator_certificate(self, weights: np.ndarray | None = None) -> float:
        """Return the Assumption 3.5 certificate from the guide's L_h-delta formula."""

        if weights is None:
            weights = self.target_support_weights
        weights = _validated_simplex_weights(weights, len(self.archive))
        archive_radii = np.array(
            [experiment.moderator_sensitivity_radius for experiment in self.archive], dtype=float
        )
        return float(
            HIDDEN_MODERATOR_LIPSCHITZ_BOUND
            * (self.target.moderator_sensitivity_radius + weights @ archive_radii)
        )

    def proxy_gap_discrepancy(self, weights: np.ndarray | None = None) -> float:
        """Evaluate the true-versus-proxy composition discrepancy for one admissible proxy mechanism."""

        if weights is None:
            weights = self.target_support_weights
        weights = _validated_simplex_weights(weights, len(self.archive))
        true_gap = self.target.true_effect - sum(
            weight * experiment.true_effect for weight, experiment in zip(weights, self.archive, strict=True)
        )
        proxy_target = effect_surface(self.target.observed_representation)
        proxy_archive = sum(
            weight * effect_surface(experiment.observed_representation)
            for weight, experiment in zip(weights, self.archive, strict=True)
        )
        return float(abs(true_gap - (proxy_target - proxy_archive)))


def effect_surface(mechanism: np.ndarray | Mechanism) -> float:
    """The smooth nonlinear effect surface specified in the paper's appendix."""

    values = _as_mechanism_array(mechanism)
    s1, s2, h, q = values
    return float(
        1.15 * np.sin(1.1 * s1)
        + 0.65 * s2
        + 1.10 * h
        + 0.45 * s1 * h
        - 0.28 * q**2
        + 0.25 * np.cos(s2 + q)
    )


def effect_gradient(mechanism: np.ndarray | Mechanism) -> np.ndarray:
    """Analytic gradient of the effect surface."""

    s1, s2, h, q = _as_mechanism_array(mechanism)
    return np.array(
        [
            1.265 * np.cos(1.1 * s1) + 0.45 * h,
            0.65 - 0.25 * np.sin(s2 + q),
            1.10 + 0.45 * s1,
            -0.56 * q - 0.25 * np.sin(s2 + q),
        ],
        dtype=float,
    )


def effect_hessian(mechanism: np.ndarray | Mechanism) -> np.ndarray:
    """Analytic Hessian used to check the H-Lipschitz gradient certificate."""

    s1, s2, _, q = _as_mechanism_array(mechanism)
    cosine_term = -0.25 * np.cos(s2 + q)
    return np.array(
        [
            [-1.3915 * np.sin(1.1 * s1), 0.0, 0.45, 0.0],
            [0.0, cosine_term, 0.0, cosine_term],
            [0.45, 0.0, 0.0, 0.0],
            [0.0, cosine_term, 0.0, -0.56 + cosine_term],
        ],
        dtype=float,
    )


def generate_minimal_archive(
    config: SimulationConfig | None = None,
    *,
    seed: int = 20260805,
) -> GeneratedArchive:
    """Generate a causally supported archive and one held-out target.

    The target mechanism is a convex combination of archive mechanisms.  The
    returned weights are oracle metadata for the sanity check only; later
    estimators must infer weights without accessing them.
    """

    config = config or SimulationConfig()
    child_seeds = np.random.SeedSequence(seed).spawn(config.n_archive + 3)
    mechanism_rng = np.random.default_rng(child_seeds[0])
    weight_rng = np.random.default_rng(child_seeds[1])

    archive_mechanisms = [
        Mechanism.from_array(
            mechanism_rng.uniform(MECHANISM_LOWER_BOUND, MECHANISM_UPPER_BOUND, size=4)
        )
        for _ in range(config.n_archive)
    ]
    target_support_weights = weight_rng.dirichlet(np.ones(config.n_archive))
    supported_target = target_support_weights @ np.vstack(
        [mechanism.as_array() for mechanism in archive_mechanisms]
    )
    # A convex move towards an in-domain anchor creates controlled semantic
    # mismatch without leaving the compact mechanism space of Assumption 3.3.
    target_mechanism = Mechanism.from_array(
        (1.0 - config.target_shift_fraction) * supported_target
        + config.target_shift_fraction * np.asarray(config.target_shift_anchor, dtype=float)
    )

    archive = tuple(
        _generate_experiment(
            experiment_id=f"archive_{index:02d}",
            mechanism=mechanism,
            n_units=config.n_units_per_experiment,
            config=config,
            rng=np.random.default_rng(child_seeds[index + 2]),
        )
        for index, mechanism in enumerate(archive_mechanisms)
    )
    target = _generate_experiment(
        experiment_id="target",
        mechanism=target_mechanism,
        n_units=config.n_units_target,
        config=config,
        rng=np.random.default_rng(child_seeds[-1]),
    )
    generated = GeneratedArchive(
        archive=archive,
        target=target,
        target_support_weights=target_support_weights,
        config=config,
    )
    assert_minimal_assumptions(generated)
    return generated


def minimal_assumption_report(generated: GeneratedArchive) -> dict[str, dict[str, Any]]:
    """Return machine-readable certificates for Assumptions 3.1--3.5."""

    experiments = (*generated.archive, generated.target)
    all_mechanisms = [experiment.mechanism.as_array() for experiment in experiments]
    gradient_norms = [float(np.linalg.norm(effect_gradient(mechanism))) for mechanism in all_mechanisms]
    hessian_norms = [
        float(np.linalg.norm(effect_hessian(mechanism), ord=2)) for mechanism in all_mechanisms
    ]
    all_observed_are_consistent = all(
        np.array_equal(
            experiment.observed_outcome,
            np.where(
                experiment.treatment == 1,
                experiment.potential_outcome_treated,
                experiment.potential_outcome_control,
            ),
        )
        for experiment in experiments
    )
    all_proxy_deviations_bounded = all(
        abs(experiment.mechanism.h - experiment.observed_representation[2])
        <= experiment.moderator_sensitivity_radius / 2.0 + 1e-12
        for experiment in experiments
    )
    all_standard_errors_match = all(
        np.isclose(
            experiment.standard_error_certificate,
            sqrt(experiment.variance_proxy / experiment.n_units),
        )
        for experiment in experiments
    )
    common_design = all(experiment.design == COMMON_DESIGN for experiment in experiments)

    return {
        "assumption_3_1_identified_experiment_effects": {
            "satisfied": bool(
                all_observed_are_consistent
                and all(
                    generated.config.overlap_lower_bound
                    <= experiment.known_propensity
                    <= 1.0 - generated.config.overlap_lower_bound
                    for experiment in experiments
                )
            ),
            "construction": "iid unit records; Bernoulli randomization with known propensity; consistency encoded as Y=A*Y(1)+(1-A)*Y(0)",
            "propensity": generated.config.propensity,
            "overlap_lower_bound": generated.config.overlap_lower_bound,
        },
        "assumption_3_2_design_compatibility_and_normalization": {
            "satisfied": bool(common_design),
            "construction": "all experiments use the same recorded DesignProfile and identity normalization",
            "common_estimand": COMMON_DESIGN.estimand,
            "outcome_scale": COMMON_DESIGN.outcome_scale,
        },
        "assumption_3_3_local_smoothness": {
            "satisfied": bool(
                all(
                    np.all(
                        (MECHANISM_LOWER_BOUND <= mechanism)
                        & (mechanism <= MECHANISM_UPPER_BOUND)
                    )
                    for mechanism in all_mechanisms
                )
                and max(gradient_norms) <= EFFECT_LIPSCHITZ_BOUND + 1e-12
                and max(hessian_norms) <= EFFECT_CURVATURE_BOUND + 1e-12
            ),
            "mechanism_space": "M=[-1,1]^4, compact and convex",
            "analytic_L_bound": EFFECT_LIPSCHITZ_BOUND,
            "analytic_H_bound": EFFECT_CURVATURE_BOUND,
            "maximum_generated_gradient_norm": max(gradient_norms),
            "maximum_generated_hessian_operator_norm": max(hessian_norms),
            "target_support_residual": generated.support_residual(),
        },
        "assumption_3_4_uncertainty_certificates": {
            "satisfied": bool(all_standard_errors_match),
            "construction": "known-nuisance AIPW score with zero nuisance remainder and independent experiment streams",
            "nuisance_bias_bound": 0.0,
            "variance_proxy_formula": "v=sigma^2/min(pi,1-pi)^2; s^2=v/n",
            "independent_experiments": True,
        },
        "assumption_3_5_observed_representation_and_moderator_certificate": {
            "satisfied": bool(
                all_proxy_deviations_bounded
                and generated.proxy_gap_discrepancy()
                <= generated.hidden_moderator_certificate() + 1e-12
            ),
            "construction": "r=(s1,s2,h_proxy,q), with a bounded h proxy and declared sensitivity radius",
            "L_h": HIDDEN_MODERATOR_LIPSCHITZ_BOUND,
            "sensitivity_radius": generated.config.moderator_sensitivity_radius,
            "R_hid": generated.hidden_moderator_certificate(),
            "proxy_gap_discrepancy": generated.proxy_gap_discrepancy(),
        },
    }


def assert_minimal_assumptions(generated: GeneratedArchive) -> None:
    """Fail fast when any construction certificate is invalid."""

    report = minimal_assumption_report(generated)
    failures = [name for name, certificate in report.items() if not certificate["satisfied"]]
    if failures:
        raise AssertionError(f"Minimal DGP failed: {', '.join(failures)}")


def _generate_experiment(
    *,
    experiment_id: str,
    mechanism: Mechanism,
    n_units: int,
    config: SimulationConfig,
    rng: np.random.Generator,
) -> ExperimentData:
    """Create one randomized, unit-level experiment with a known AIPW certificate."""

    true_effect = effect_surface(mechanism)
    covariates = rng.normal(loc=0.0, scale=1.0, size=(n_units, 2))
    baseline_outcome = 0.50 * covariates[:, 0] - 0.30 * covariates[:, 1]
    error_control = rng.normal(loc=0.0, scale=config.outcome_noise_sd, size=n_units)
    error_treated = rng.normal(loc=0.0, scale=config.outcome_noise_sd, size=n_units)
    potential_outcome_control = baseline_outcome + error_control
    potential_outcome_treated = baseline_outcome + true_effect + error_treated
    treatment = rng.binomial(1, config.propensity, size=n_units).astype(np.int8)
    observed_outcome = np.where(treatment == 1, potential_outcome_treated, potential_outcome_control)

    nuisance_control = baseline_outcome
    nuisance_treated = baseline_outcome + true_effect
    aipw_scores = (
        nuisance_treated
        - nuisance_control
        + treatment * (observed_outcome - nuisance_treated) / config.propensity
        - (1 - treatment)
        * (observed_outcome - nuisance_control)
        / (1.0 - config.propensity)
    )
    variance_proxy = config.outcome_noise_sd**2 / min(
        config.propensity, 1.0 - config.propensity
    ) ** 2
    proxy_error = rng.uniform(
        -config.moderator_proxy_half_width,
        config.moderator_proxy_half_width,
    )
    moderator_proxy = float(
        np.clip(
            mechanism.h + proxy_error,
            MECHANISM_LOWER_BOUND,
            MECHANISM_UPPER_BOUND,
        )
    )

    return ExperimentData(
        experiment_id=experiment_id,
        mechanism=mechanism,
        observed_representation=np.array(
            [mechanism.s1, mechanism.s2, moderator_proxy, mechanism.q], dtype=float
        ),
        design=COMMON_DESIGN,
        x=covariates,
        treatment=treatment,
        observed_outcome=observed_outcome,
        potential_outcome_control=potential_outcome_control,
        potential_outcome_treated=potential_outcome_treated,
        aipw_scores=aipw_scores,
        true_effect=true_effect,
        estimated_effect=float(np.mean(aipw_scores)),
        variance_proxy=float(variance_proxy),
        standard_error_certificate=float(sqrt(variance_proxy / n_units)),
        nuisance_bias_bound=0.0,
        known_propensity=config.propensity,
        moderator_sensitivity_radius=config.moderator_sensitivity_radius,
    )


def _as_mechanism_array(mechanism: np.ndarray | Mechanism) -> np.ndarray:
    values = mechanism.as_array() if isinstance(mechanism, Mechanism) else np.asarray(mechanism)
    values = np.asarray(values, dtype=float)
    if values.shape != (4,):
        raise ValueError("A mechanism must have shape (4,).")
    return values


def _validated_simplex_weights(weights: np.ndarray, n_archive: int) -> np.ndarray:
    weights = np.asarray(weights, dtype=float)
    if weights.shape != (n_archive,):
        raise ValueError("Weights must have one entry per archive experiment.")
    if np.any(weights < -1e-12) or not np.isclose(weights.sum(), 1.0):
        raise ValueError("Weights must be nonnegative and sum to one.")
    return weights
