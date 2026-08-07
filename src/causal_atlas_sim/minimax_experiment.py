"""Theorem 5.5 two-point minimax lower-bound experiment.

The experiment deliberately uses the Gaussian submodels from the proof rather
than the nonlinear AIPW data-generating process used by Stages 1--9.  This is
the appropriate construction for a minimax lower bound: each submodel is a
valid restricted part of the larger model class, so its indistinguishability
is inherited by the full problem.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import erf, exp, pi, sqrt
from typing import Any

import numpy as np

from .dgp import EFFECT_ABSOLUTE_BOUND, EFFECT_LIPSCHITZ_BOUND


@dataclass(frozen=True)
class MinimaxScenario:
    """One combination of unsupported-target distance and archive noise."""

    key: str
    label: str
    hull_distance: float
    archive_standard_error: float

    def __post_init__(self) -> None:
        if not self.key or not self.label:
            raise ValueError("A minimax scenario needs a key and label.")
        if self.hull_distance < 0.0:
            raise ValueError("hull_distance must be nonnegative.")
        if self.archive_standard_error <= 0.0:
            raise ValueError("archive_standard_error must be positive.")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_minimax_scenarios() -> tuple[MinimaxScenario, ...]:
    """Return fixed distance and precision settings for the proof submodels."""

    distances = (
        ("d000", "d_star = 0.00", 0.00),
        ("d025", "d_star = 0.25", 0.25),
        ("d060", "d_star = 0.60", 0.60),
        ("d100", "d_star = 1.00", 1.00),
    )
    precisions = (
        ("precise", "precise archive (s = 0.35)", 0.35),
        ("noisy", "noisy archive (s = 1.20)", 1.20),
    )
    return tuple(
        MinimaxScenario(
            key=f"{distance_key}_{precision_key}",
            label=f"{distance_label}; {precision_label}",
            hull_distance=distance,
            archive_standard_error=standard_error,
        )
        for distance_key, distance_label, distance in distances
        for precision_key, precision_label, standard_error in precisions
    )


@dataclass(frozen=True)
class MinimaxExperimentConfig:
    """Fixed multi-seed protocol for the Theorem 5.5 illustration."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20261011, 20261012, 20261013)
    scenarios: tuple[MinimaxScenario, ...] = field(
        default_factory=default_minimax_scenarios
    )
    archive_count: int = 8
    effect_lipschitz_bound: float = EFFECT_LIPSCHITZ_BOUND
    effect_absolute_bound: float = EFFECT_ABSOLUTE_BOUND
    le_cam_constant: float = 0.25

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2:
            raise ValueError("At least two repetitions per seed are required.")
        if not self.base_seeds or not self.scenarios:
            raise ValueError("Seeds and scenarios must be nonempty.")
        if self.archive_count < 1:
            raise ValueError("archive_count must be positive.")
        if self.effect_lipschitz_bound <= 0.0:
            raise ValueError("effect_lipschitz_bound must be positive.")
        if self.effect_absolute_bound <= 0.0:
            raise ValueError("effect_absolute_bound must be positive.")
        if not 0.0 < self.le_cam_constant < 1.0:
            raise ValueError("le_cam_constant must lie in (0, 1).")


@dataclass(frozen=True)
class MinimaxParameters:
    """Derived scales of the two lower-bound constructions."""

    hull_distance: float
    archive_standard_error: float
    archive_count: int
    information: float
    estimator_standard_error: float
    geometric_scale: float
    geometric_alternative_magnitude: float
    geometric_lower_bound: float
    information_scale: float
    statistical_alternative_magnitude: float
    statistical_lower_bound: float
    combined_lower_bound: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def minimax_parameters(
    scenario: MinimaxScenario,
    config: MinimaxExperimentConfig,
) -> MinimaxParameters:
    """Compute the exact scales used in the Theorem 5.5 proof construction."""

    information = config.archive_count / scenario.archive_standard_error**2
    estimator_standard_error = 1.0 / sqrt(information)
    geometric_scale = min(
        config.effect_lipschitz_bound * scenario.hull_distance,
        config.effect_absolute_bound,
    )
    geometric_magnitude = 0.25 * geometric_scale
    information_scale = min(
        estimator_standard_error,
        config.effect_absolute_bound,
    )
    statistical_magnitude = config.le_cam_constant * information_scale
    statistical_lower_bound = (
        config.le_cam_constant
        * (1.0 - config.le_cam_constant)
        / 2.0
        * information_scale
    )
    geometric_lower_bound = geometric_magnitude
    return MinimaxParameters(
        hull_distance=scenario.hull_distance,
        archive_standard_error=scenario.archive_standard_error,
        archive_count=config.archive_count,
        information=information,
        estimator_standard_error=estimator_standard_error,
        geometric_scale=geometric_scale,
        geometric_alternative_magnitude=geometric_magnitude,
        geometric_lower_bound=geometric_lower_bound,
        information_scale=information_scale,
        statistical_alternative_magnitude=statistical_magnitude,
        statistical_lower_bound=statistical_lower_bound,
        combined_lower_bound=max(geometric_lower_bound, statistical_lower_bound),
    )


def geometric_surface_value(
    location: float,
    scenario: MinimaxScenario,
    parameters: MinimaxParameters,
    sign: int,
) -> float:
    """Return the bounded Lipschitz ramp used by the geometric pair.

    Archive mechanisms are fixed at location zero and the target is at
    ``scenario.hull_distance``.  The two signed ramps agree at the archive
    while taking opposite target values.  Their Lipschitz constants are at
    most one fourth of the configured theorem constant.
    """

    if sign not in {-1, 1}:
        raise ValueError("sign must be either -1 or 1.")
    if scenario.hull_distance == 0.0:
        return 0.0
    fraction = min(max(location / scenario.hull_distance, 0.0), 1.0)
    return float(sign * parameters.geometric_alternative_magnitude * fraction)


@dataclass(frozen=True)
class MinimaxRecord:
    """One paired simulation of the geometric and statistical submodels."""

    scenario_key: str
    scenario_label: str
    seed_batch: int
    replicate: int
    seed: int
    geometric_positive_absolute_error: float
    geometric_negative_absolute_error: float
    statistical_positive_absolute_error: float
    statistical_negative_absolute_error: float


@dataclass(frozen=True)
class MinimaxSummaryRow:
    """Lower-bound scales and representative-estimator risks for one scenario."""

    scenario_key: str
    scenario_label: str
    repetitions: int
    seed_batches: int
    hull_distance: float
    archive_standard_error: float
    archive_count: int
    information: float
    estimator_standard_error: float
    geometric_scale: float
    geometric_lower_bound: float
    information_scale: float
    statistical_lower_bound: float
    combined_lower_bound: float
    empirical_geometric_worst_mae: float
    analytic_geometric_worst_mae: float
    empirical_statistical_worst_mae: float
    analytic_statistical_worst_mae: float
    empirical_worst_case_mae: float
    analytic_worst_case_mae: float
    empirical_to_lower_bound_ratio: float
    between_seed_worst_case_mae_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MinimaxExperimentResult:
    """Records and summaries from the fixed Theorem 5.5 protocol."""

    config: MinimaxExperimentConfig
    records: tuple[MinimaxRecord, ...]
    rows: tuple[MinimaxSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "scenarios": [scenario.as_dict() for scenario in self.config.scenarios],
                "archive_count": self.config.archive_count,
                "effect_lipschitz_bound": self.config.effect_lipschitz_bound,
                "effect_absolute_bound": self.config.effect_absolute_bound,
                "le_cam_constant": self.config.le_cam_constant,
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_minimax_experiment(
    config: MinimaxExperimentConfig | None = None,
) -> MinimaxExperimentResult:
    """Run the two independent proof submodels with shared fixed seeds."""

    config = config or MinimaxExperimentConfig()
    records: list[MinimaxRecord] = []
    for scenario in config.scenarios:
        parameters = minimax_parameters(scenario, config)
        standard_errors = np.full(
            config.archive_count,
            scenario.archive_standard_error,
            dtype=float,
        )
        for seed_batch, base_seed in enumerate(config.base_seeds):
            sequences = np.random.SeedSequence(base_seed).spawn(
                config.repetitions_per_seed
            )
            for replicate, sequence in enumerate(sequences):
                seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
                rng = np.random.default_rng(seed)

                # The geometric pair has exactly the same archive distribution.
                geometric_observations = standard_errors * rng.normal(
                    size=config.archive_count
                )
                geometric_estimate = _inverse_variance_estimate(
                    geometric_observations,
                    standard_errors,
                )

                # These are independent draws from the two constant-surface worlds.
                statistical_positive_observations = (
                    parameters.statistical_alternative_magnitude
                    + standard_errors * rng.normal(size=config.archive_count)
                )
                statistical_negative_observations = (
                    -parameters.statistical_alternative_magnitude
                    + standard_errors * rng.normal(size=config.archive_count)
                )
                statistical_positive_estimate = _inverse_variance_estimate(
                    statistical_positive_observations,
                    standard_errors,
                )
                statistical_negative_estimate = _inverse_variance_estimate(
                    statistical_negative_observations,
                    standard_errors,
                )
                records.append(
                    MinimaxRecord(
                        scenario_key=scenario.key,
                        scenario_label=scenario.label,
                        seed_batch=seed_batch,
                        replicate=replicate,
                        seed=seed,
                        geometric_positive_absolute_error=abs(
                            geometric_estimate
                            - parameters.geometric_alternative_magnitude
                        ),
                        geometric_negative_absolute_error=abs(
                            geometric_estimate
                            + parameters.geometric_alternative_magnitude
                        ),
                        statistical_positive_absolute_error=abs(
                            statistical_positive_estimate
                            - parameters.statistical_alternative_magnitude
                        ),
                        statistical_negative_absolute_error=abs(
                            statistical_negative_estimate
                            + parameters.statistical_alternative_magnitude
                        ),
                    )
                )
    return MinimaxExperimentResult(
        config=config,
        records=tuple(records),
        rows=_summarize_records(records, config),
    )


def _inverse_variance_estimate(
    observations: np.ndarray,
    standard_errors: np.ndarray,
) -> float:
    weights = standard_errors**-2
    return float(np.dot(weights, observations) / weights.sum())


def _summarize_records(
    records: list[MinimaxRecord],
    config: MinimaxExperimentConfig,
) -> tuple[MinimaxSummaryRow, ...]:
    return tuple(
        _summarize_one(
            scenario,
            [record for record in records if record.scenario_key == scenario.key],
            config,
        )
        for scenario in config.scenarios
    )


def _summarize_one(
    scenario: MinimaxScenario,
    records: list[MinimaxRecord],
    config: MinimaxExperimentConfig,
) -> MinimaxSummaryRow:
    if not records:
        raise ValueError("Cannot summarize an empty minimax scenario.")
    parameters = minimax_parameters(scenario, config)
    geometric_worst = max(
        _mean(records, "geometric_positive_absolute_error"),
        _mean(records, "geometric_negative_absolute_error"),
    )
    statistical_worst = max(
        _mean(records, "statistical_positive_absolute_error"),
        _mean(records, "statistical_negative_absolute_error"),
    )
    empirical_worst = max(geometric_worst, statistical_worst)
    analytic_geometric = _normal_absolute_deviation(
        parameters.geometric_alternative_magnitude,
        parameters.estimator_standard_error,
    )
    analytic_statistical = parameters.estimator_standard_error * sqrt(2.0 / pi)
    analytic_worst = max(analytic_geometric, analytic_statistical)
    seed_worst_cases = []
    for seed_batch in sorted({record.seed_batch for record in records}):
        batch = [record for record in records if record.seed_batch == seed_batch]
        batch_geometric = max(
            _mean(batch, "geometric_positive_absolute_error"),
            _mean(batch, "geometric_negative_absolute_error"),
        )
        batch_statistical = max(
            _mean(batch, "statistical_positive_absolute_error"),
            _mean(batch, "statistical_negative_absolute_error"),
        )
        seed_worst_cases.append(max(batch_geometric, batch_statistical))
    return MinimaxSummaryRow(
        scenario_key=scenario.key,
        scenario_label=scenario.label,
        repetitions=len(records),
        seed_batches=len(seed_worst_cases),
        hull_distance=parameters.hull_distance,
        archive_standard_error=parameters.archive_standard_error,
        archive_count=parameters.archive_count,
        information=parameters.information,
        estimator_standard_error=parameters.estimator_standard_error,
        geometric_scale=parameters.geometric_scale,
        geometric_lower_bound=parameters.geometric_lower_bound,
        information_scale=parameters.information_scale,
        statistical_lower_bound=parameters.statistical_lower_bound,
        combined_lower_bound=parameters.combined_lower_bound,
        empirical_geometric_worst_mae=geometric_worst,
        analytic_geometric_worst_mae=analytic_geometric,
        empirical_statistical_worst_mae=statistical_worst,
        analytic_statistical_worst_mae=analytic_statistical,
        empirical_worst_case_mae=empirical_worst,
        analytic_worst_case_mae=analytic_worst,
        empirical_to_lower_bound_ratio=(
            empirical_worst / parameters.combined_lower_bound
        ),
        between_seed_worst_case_mae_sd=(
            float(np.std(seed_worst_cases, ddof=1))
            if len(seed_worst_cases) > 1
            else None
        ),
    )


def _mean(records: list[MinimaxRecord], field_name: str) -> float:
    return float(np.mean([getattr(record, field_name) for record in records]))


def _normal_absolute_deviation(offset: float, standard_error: float) -> float:
    """Return E|Z - offset| for Z distributed as N(0, standard_error^2)."""

    standardized = offset / standard_error
    return (
        standard_error
        * sqrt(2.0 / pi)
        * exp(-0.5 * standardized**2)
        + offset * erf(standardized / sqrt(2.0))
    )
