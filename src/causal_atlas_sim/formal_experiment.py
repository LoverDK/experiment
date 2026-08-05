"""Multi-seed formal benchmark, ablation, and sensitivity protocol."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from math import sqrt
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .methods import METHODS, AtlasConfig, AtlasResult, fit_method


@dataclass(frozen=True)
class FormalScenario:
    """One preregistered scenario relative to the nominal DGP."""

    key: str
    label: str
    semantic_shift_fraction: float = 0.0
    moderator_sensitivity_radius: float = 0.20
    sample_size: int = 400
    scientific_tolerance: float = 1.65

    def __post_init__(self) -> None:
        if not self.key or not self.label:
            raise ValueError("A formal scenario needs a key and label.")
        if not 0.0 <= self.semantic_shift_fraction <= 1.0:
            raise ValueError("semantic_shift_fraction must lie in [0, 1].")
        if self.moderator_sensitivity_radius < 0.20:
            raise ValueError("moderator_sensitivity_radius must cover the proxy diameter.")
        if self.sample_size < 20:
            raise ValueError("sample_size must be at least 20.")
        if self.scientific_tolerance < 0.0:
            raise ValueError("scientific_tolerance must be nonnegative.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "semantic_shift_fraction": self.semantic_shift_fraction,
            "moderator_sensitivity_radius": self.moderator_sensitivity_radius,
            "sample_size": self.sample_size,
            "scientific_tolerance": self.scientific_tolerance,
        }


def default_formal_scenarios() -> tuple[FormalScenario, ...]:
    """Return the nominal, stress, and sample-size scenarios."""

    return (
        FormalScenario("nominal", "nominal setting"),
        FormalScenario(
            "semantic_mismatch_010",
            "mild semantic mismatch",
            semantic_shift_fraction=0.10,
        ),
        FormalScenario(
            "semantic_mismatch_025",
            "severe semantic mismatch",
            semantic_shift_fraction=0.25,
        ),
        FormalScenario(
            "hidden_radius_040",
            "larger hidden-moderator uncertainty",
            moderator_sensitivity_radius=0.40,
        ),
        FormalScenario("sample_size_100", "small experiments", sample_size=100),
        FormalScenario("sample_size_1000", "large experiments", sample_size=1000),
    )


@dataclass(frozen=True)
class FormalEstimator:
    """An estimator or one controlled implementation ablation."""

    key: str
    method: str
    lambda_sigma: float | None = None
    max_candidates: int | None = None

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("An estimator needs a key.")
        if self.method not in METHODS:
            raise ValueError(f"Unknown method: {self.method}")
        if self.lambda_sigma is not None and self.lambda_sigma < 0.0:
            raise ValueError("lambda_sigma must be nonnegative.")
        if self.max_candidates is not None and self.max_candidates < 1:
            raise ValueError("max_candidates must be positive.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "method": self.method,
            "lambda_sigma": self.lambda_sigma,
            "max_candidates": self.max_candidates,
        }


def default_formal_estimators() -> tuple[FormalEstimator, ...]:
    """Return the main method, ablations, and comparison baselines."""

    return (
        FormalEstimator("atlas", "atlas"),
        FormalEstimator("atlas_no_rejection", "atlas_no_rejection"),
        FormalEstimator("atlas_no_variance_penalty", "atlas", lambda_sigma=0.0),
        FormalEstimator("atlas_top4_candidates", "atlas", max_candidates=4),
        FormalEstimator("semantic_forced", "semantic_forced"),
        FormalEstimator("nearest_semantic", "nearest_semantic"),
        FormalEstimator("global_mean", "global_mean"),
    )


@dataclass(frozen=True)
class FormalExperimentConfig:
    """Controls the multi-seed formal run."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260811, 20260812, 20260813)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    scenarios: tuple[FormalScenario, ...] = field(
        default_factory=default_formal_scenarios
    )
    estimators: tuple[FormalEstimator, ...] = field(
        default_factory=default_formal_estimators
    )
    z_value: float = 1.96

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2:
            raise ValueError("At least two repetitions per seed are required.")
        if not self.base_seeds:
            raise ValueError("At least one base seed is required.")
        if not self.scenarios or not self.estimators:
            raise ValueError("At least one scenario and estimator are required.")
        if self.z_value <= 0.0:
            raise ValueError("z_value must be positive.")


@dataclass(frozen=True)
class FormalRecord:
    """One estimator output for one shared target draw."""

    scenario_key: str
    scenario_label: str
    estimator_key: str
    seed_batch: int
    replicate: int
    seed: int
    target_true_effect: float
    result: AtlasResult


@dataclass(frozen=True)
class FormalSummaryRow:
    """Pooled and between-seed metrics for one scenario-estimator pair."""

    scenario_key: str
    scenario_label: str
    estimator_key: str
    repetitions: int
    seed_batches: int
    accepted_repetitions: int
    acceptance_rate: float
    acceptance_ci_lower: float
    acceptance_ci_upper: float
    rejection_rate: float
    accepted_mae: float | None
    accepted_mae_mc_se: float | None
    accepted_rmse: float | None
    accepted_bias: float | None
    accepted_sign_accuracy: float | None
    interval_coverage: float | None
    mean_interval_width: float | None
    mean_certificate_radius: float | None
    between_seed_acceptance_sd: float | None
    between_seed_mae_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_key": self.scenario_key,
            "scenario_label": self.scenario_label,
            "estimator_key": self.estimator_key,
            "repetitions": self.repetitions,
            "seed_batches": self.seed_batches,
            "accepted_repetitions": self.accepted_repetitions,
            "acceptance_rate": self.acceptance_rate,
            "acceptance_ci_lower": self.acceptance_ci_lower,
            "acceptance_ci_upper": self.acceptance_ci_upper,
            "rejection_rate": self.rejection_rate,
            "accepted_mae": self.accepted_mae,
            "accepted_mae_mc_se": self.accepted_mae_mc_se,
            "accepted_rmse": self.accepted_rmse,
            "accepted_bias": self.accepted_bias,
            "accepted_sign_accuracy": self.accepted_sign_accuracy,
            "interval_coverage": self.interval_coverage,
            "mean_interval_width": self.mean_interval_width,
            "mean_certificate_radius": self.mean_certificate_radius,
            "between_seed_acceptance_sd": self.between_seed_acceptance_sd,
            "between_seed_mae_sd": self.between_seed_mae_sd,
        }


@dataclass(frozen=True)
class FormalExperimentResult:
    """Formal records and the paper-facing summary table."""

    config: FormalExperimentConfig
    records: tuple[FormalRecord, ...]
    rows: tuple[FormalSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "z_value": self.config.z_value,
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
                "scenarios": [scenario.as_dict() for scenario in self.config.scenarios],
                "estimators": [estimator.as_dict() for estimator in self.config.estimators],
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_formal_experiment(
    config: FormalExperimentConfig | None = None,
) -> FormalExperimentResult:
    """Run each scenario with shared draws across all estimators."""

    config = config or FormalExperimentConfig()
    records: list[FormalRecord] = []
    for scenario in config.scenarios:
        dgp_config = replace(
            config.dgp_config,
            target_shift_fraction=scenario.semantic_shift_fraction,
            moderator_sensitivity_radius=scenario.moderator_sensitivity_radius,
            n_units_per_experiment=scenario.sample_size,
            n_units_target=scenario.sample_size,
        )
        atlas_config = replace(
            config.atlas_config,
            scientific_tolerance=scenario.scientific_tolerance,
        )
        for seed_batch, base_seed in enumerate(config.base_seeds):
            seed_sequences = np.random.SeedSequence(base_seed).spawn(
                config.repetitions_per_seed
            )
            for replicate, sequence in enumerate(seed_sequences):
                seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
                generated = generate_minimal_archive(dgp_config, seed=seed)
                for estimator in config.estimators:
                    estimator_config = _estimator_config(atlas_config, estimator)
                    result = fit_method(
                        estimator.method,
                        generated.archive,
                        generated.target,
                        estimator_config,
                    )
                    records.append(
                        FormalRecord(
                            scenario_key=scenario.key,
                            scenario_label=scenario.label,
                            estimator_key=estimator.key,
                            seed_batch=seed_batch,
                            replicate=replicate,
                            seed=seed,
                            target_true_effect=generated.target.true_effect,
                            result=result,
                        )
                    )
    rows = _summarize_records(records, config)
    return FormalExperimentResult(config=config, records=tuple(records), rows=rows)


def _estimator_config(
    atlas_config: AtlasConfig,
    estimator: FormalEstimator,
) -> AtlasConfig:
    updates: dict[str, Any] = {}
    if estimator.lambda_sigma is not None:
        updates["lambda_sigma"] = estimator.lambda_sigma
    if estimator.max_candidates is not None:
        updates["max_candidates"] = estimator.max_candidates
    return replace(atlas_config, **updates)


def _summarize_records(
    records: list[FormalRecord],
    config: FormalExperimentConfig,
) -> tuple[FormalSummaryRow, ...]:
    rows: list[FormalSummaryRow] = []
    for scenario in config.scenarios:
        for estimator in config.estimators:
            selected = [
                record
                for record in records
                if record.scenario_key == scenario.key
                and record.estimator_key == estimator.key
            ]
            rows.append(_summarize_one(scenario, estimator, selected, config.z_value))
    return tuple(rows)


def _summarize_one(
    scenario: FormalScenario,
    estimator: FormalEstimator,
    records: list[FormalRecord],
    z_value: float,
) -> FormalSummaryRow:
    results = [record.result for record in records]
    accepted_records = [
        record for record in records if record.result.point_estimate is not None
    ]
    errors = np.asarray(
        [
            record.result.point_estimate - record.target_true_effect
            for record in accepted_records
        ],
        dtype=float,
    )
    interval_records = [
        record
        for record in records
        if np.isfinite(record.result.interval_lower)
        and np.isfinite(record.result.interval_upper)
    ]
    coverage = [
        record.result.interval_lower
        <= record.target_true_effect
        <= record.result.interval_upper
        for record in interval_records
    ]
    acceptance_rate = float(np.mean([result.accepted for result in results]))
    acceptance_ci_lower, acceptance_ci_upper = wilson_interval(
        sum(result.accepted for result in results),
        len(results),
        z_value,
    )
    by_seed = [
        [record for record in records if record.seed_batch == seed_batch]
        for seed_batch in sorted({record.seed_batch for record in records})
    ]
    seed_acceptance = [
        float(np.mean([record.result.accepted for record in batch]))
        for batch in by_seed
    ]
    seed_mae = [
        float(
            np.mean(
                [
                    abs(record.result.point_estimate - record.target_true_effect)
                    for record in batch
                    if record.result.point_estimate is not None
                ]
            )
        )
        for batch in by_seed
        if any(record.result.point_estimate is not None for record in batch)
    ]
    finite_certificates = [
        record.result.certificate.radius
        for record in records
        if np.isfinite(record.result.certificate.radius)
    ]
    return FormalSummaryRow(
        scenario_key=scenario.key,
        scenario_label=scenario.label,
        estimator_key=estimator.key,
        repetitions=len(records),
        seed_batches=len(by_seed),
        accepted_repetitions=len(accepted_records),
        acceptance_rate=acceptance_rate,
        acceptance_ci_lower=acceptance_ci_lower,
        acceptance_ci_upper=acceptance_ci_upper,
        rejection_rate=float(np.mean([result.rejected for result in results])),
        accepted_mae=float(np.mean(np.abs(errors))) if errors.size else None,
        accepted_mae_mc_se=(
            float(np.std(np.abs(errors), ddof=1) / sqrt(errors.size))
            if errors.size > 1
            else None
        ),
        accepted_rmse=float(np.sqrt(np.mean(errors**2))) if errors.size else None,
        accepted_bias=float(np.mean(errors)) if errors.size else None,
        accepted_sign_accuracy=(
            float(
                np.mean(
                    [
                        np.sign(record.result.point_estimate)
                        == np.sign(record.target_true_effect)
                        for record in accepted_records
                    ]
                )
            )
            if accepted_records
            else None
        ),
        interval_coverage=float(np.mean(coverage)) if coverage else None,
        mean_interval_width=(
            float(
                np.mean(
                    [
                        record.result.interval_upper - record.result.interval_lower
                        for record in interval_records
                    ]
                )
            )
            if interval_records
            else None
        ),
        mean_certificate_radius=(
            float(np.mean(finite_certificates)) if finite_certificates else None
        ),
        between_seed_acceptance_sd=(
            float(np.std(seed_acceptance, ddof=1))
            if len(seed_acceptance) > 1
            else None
        ),
        between_seed_mae_sd=(
            float(np.std(seed_mae, ddof=1)) if len(seed_mae) > 1 else None
        ),
    )


def wilson_interval(
    successes: int,
    trials: int,
    z_value: float = 1.96,
) -> tuple[float, float]:
    """Return a Wilson score interval for a binomial proportion."""

    if trials < 1 or not 0 <= successes <= trials:
        raise ValueError("successes and trials must define a valid binomial count.")
    if z_value <= 0.0:
        raise ValueError("z_value must be positive.")
    proportion = successes / trials
    z_squared = z_value**2
    denominator = 1.0 + z_squared / trials
    center = (proportion + z_squared / (2.0 * trials)) / denominator
    half_width = (
        z_value
        * sqrt(
            proportion * (1.0 - proportion) / trials
            + z_squared / (4.0 * trials**2)
        )
        / denominator
    )
    lower = 0.0 if successes == 0 else max(0.0, center - half_width)
    upper = 1.0 if successes == trials else min(1.0, center + half_width)
    return lower, upper
