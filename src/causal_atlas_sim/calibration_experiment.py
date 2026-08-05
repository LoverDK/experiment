"""Certificate calibration and failure-boundary simulations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from math import sqrt
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .formal_experiment import wilson_interval
from .methods import AtlasConfig, AtlasResult, fit_method


@dataclass(frozen=True)
class CalibrationScenario:
    """A stress scenario that preserves the DGP's core assumptions."""

    key: str
    label: str
    semantic_shift_fraction: float = 0.0
    archive_moderator_radius_spread: float = 0.0
    scientific_tolerance: float = 1.65

    def __post_init__(self) -> None:
        if not self.key or not self.label:
            raise ValueError("A calibration scenario needs a key and label.")
        if not 0.0 <= self.semantic_shift_fraction <= 1.0:
            raise ValueError("semantic_shift_fraction must lie in [0, 1].")
        if self.archive_moderator_radius_spread < 0.0:
            raise ValueError("archive_moderator_radius_spread must be nonnegative.")
        if self.scientific_tolerance < 0.0:
            raise ValueError("scientific_tolerance must be nonnegative.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "semantic_shift_fraction": self.semantic_shift_fraction,
            "archive_moderator_radius_spread": self.archive_moderator_radius_spread,
            "scientific_tolerance": self.scientific_tolerance,
        }


def default_calibration_scenarios() -> tuple[CalibrationScenario, ...]:
    """Return nominal, heterogeneous, and strong-mismatch stress cases."""

    return (
        CalibrationScenario("nominal", "nominal certified setting"),
        CalibrationScenario(
            "heterogeneous_hidden_radii",
            "heterogeneous archive hidden radii",
            archive_moderator_radius_spread=0.40,
        ),
        CalibrationScenario(
            "strong_semantic_mismatch",
            "strong semantic mismatch",
            semantic_shift_fraction=0.60,
        ),
        CalibrationScenario(
            "severe_semantic_mismatch",
            "severe semantic mismatch",
            semantic_shift_fraction=0.80,
        ),
    )


@dataclass(frozen=True)
class CalibrationPolicy:
    """A point-release policy and the bounds supplied to its certificate."""

    key: str
    label: str
    method: str
    effect_lipschitz_bound: float | None = None
    effect_curvature_bound: float | None = None

    def __post_init__(self) -> None:
        if self.method not in {"atlas", "atlas_no_rejection"}:
            raise ValueError("Calibration policies must use atlas or atlas_no_rejection.")
        if not self.key or not self.label:
            raise ValueError("A calibration policy needs a key and label.")
        if (
            self.effect_lipschitz_bound is not None
            and self.effect_lipschitz_bound <= 0.0
        ):
            raise ValueError("effect_lipschitz_bound must be positive.")
        if (
            self.effect_curvature_bound is not None
            and self.effect_curvature_bound <= 0.0
        ):
            raise ValueError("effect_curvature_bound must be positive.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "method": self.method,
            "effect_lipschitz_bound": self.effect_lipschitz_bound,
            "effect_curvature_bound": self.effect_curvature_bound,
        }


def default_calibration_policies() -> tuple[CalibrationPolicy, ...]:
    """Return certified, no-rejection, and intentionally underreported policies."""

    return (
        CalibrationPolicy("certified_atlas", "certified ATLAS", "atlas"),
        CalibrationPolicy(
            "no_rejection",
            "no-rejection ablation",
            "atlas_no_rejection",
        ),
        CalibrationPolicy(
            "understated_smoothness",
            "understated smoothness bounds",
            "atlas",
            effect_lipschitz_bound=0.20,
            effect_curvature_bound=0.05,
        ),
    )


@dataclass(frozen=True)
class CalibrationExperimentConfig:
    """Controls the multi-seed certificate calibration experiment."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260831, 20260901, 20260902)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    scenarios: tuple[CalibrationScenario, ...] = field(
        default_factory=default_calibration_scenarios
    )
    policies: tuple[CalibrationPolicy, ...] = field(
        default_factory=default_calibration_policies
    )
    z_value: float = 1.96

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2:
            raise ValueError("At least two repetitions per seed are required.")
        if not self.base_seeds:
            raise ValueError("At least one base seed is required.")
        if not self.scenarios or not self.policies:
            raise ValueError("At least one scenario and policy are required.")
        if self.z_value <= 0.0:
            raise ValueError("z_value must be positive.")


@dataclass(frozen=True)
class CalibrationRecord:
    """One policy output on one shared DGP draw."""

    scenario_key: str
    scenario_label: str
    policy_key: str
    seed_batch: int
    replicate: int
    seed: int
    target_true_effect: float
    scientific_tolerance: float
    result: AtlasResult


@dataclass(frozen=True)
class CalibrationSummaryRow:
    """Release, error, and interval-calibration metrics for one policy."""

    scenario_key: str
    scenario_label: str
    policy_key: str
    repetitions: int
    seed_batches: int
    released_repetitions: int
    release_rate: float
    release_ci_lower: float
    release_ci_upper: float
    mean_raw_mae: float | None
    released_mae: float | None
    released_interval_coverage: float | None
    released_interval_uncovered_rate: float | None
    released_above_tolerance_rate: float | None
    overall_interval_coverage: float | None
    mean_certificate_radius: float | None
    between_seed_release_sd: float | None
    between_seed_released_coverage_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_key": self.scenario_key,
            "scenario_label": self.scenario_label,
            "policy_key": self.policy_key,
            "repetitions": self.repetitions,
            "seed_batches": self.seed_batches,
            "released_repetitions": self.released_repetitions,
            "release_rate": self.release_rate,
            "release_ci_lower": self.release_ci_lower,
            "release_ci_upper": self.release_ci_upper,
            "mean_raw_mae": self.mean_raw_mae,
            "released_mae": self.released_mae,
            "released_interval_coverage": self.released_interval_coverage,
            "released_interval_uncovered_rate": self.released_interval_uncovered_rate,
            "released_above_tolerance_rate": self.released_above_tolerance_rate,
            "overall_interval_coverage": self.overall_interval_coverage,
            "mean_certificate_radius": self.mean_certificate_radius,
            "between_seed_release_sd": self.between_seed_release_sd,
            "between_seed_released_coverage_sd": self.between_seed_released_coverage_sd,
        }


@dataclass(frozen=True)
class CalibrationExperimentResult:
    """All shared records and calibration summary rows."""

    config: CalibrationExperimentConfig
    records: tuple[CalibrationRecord, ...]
    rows: tuple[CalibrationSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "z_value": self.config.z_value,
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
                "scenarios": [scenario.as_dict() for scenario in self.config.scenarios],
                "policies": [policy.as_dict() for policy in self.config.policies],
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_calibration_experiment(
    config: CalibrationExperimentConfig | None = None,
) -> CalibrationExperimentResult:
    """Run every policy on shared draws for every calibration scenario."""

    config = config or CalibrationExperimentConfig()
    records: list[CalibrationRecord] = []
    for scenario in config.scenarios:
        dgp_config = replace(
            config.dgp_config,
            target_shift_fraction=scenario.semantic_shift_fraction,
            archive_moderator_radius_spread=scenario.archive_moderator_radius_spread,
        )
        base_atlas_config = replace(
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
                for policy in config.policies:
                    result = fit_method(
                        policy.method,
                        generated.archive,
                        generated.target,
                        _policy_config(base_atlas_config, policy),
                    )
                    records.append(
                        CalibrationRecord(
                            scenario_key=scenario.key,
                            scenario_label=scenario.label,
                            policy_key=policy.key,
                            seed_batch=seed_batch,
                            replicate=replicate,
                            seed=seed,
                            target_true_effect=generated.target.true_effect,
                            scientific_tolerance=scenario.scientific_tolerance,
                            result=result,
                        )
                    )
    return CalibrationExperimentResult(
        config=config,
        records=tuple(records),
        rows=_summarize_records(records, config),
    )


def _policy_config(
    atlas_config: AtlasConfig,
    policy: CalibrationPolicy,
) -> AtlasConfig:
    updates: dict[str, Any] = {}
    if policy.effect_lipschitz_bound is not None:
        updates["effect_lipschitz_bound"] = policy.effect_lipschitz_bound
    if policy.effect_curvature_bound is not None:
        updates["effect_curvature_bound"] = policy.effect_curvature_bound
    return replace(atlas_config, **updates)


def _summarize_records(
    records: list[CalibrationRecord],
    config: CalibrationExperimentConfig,
) -> tuple[CalibrationSummaryRow, ...]:
    rows: list[CalibrationSummaryRow] = []
    for scenario in config.scenarios:
        for policy in config.policies:
            selected = [
                record
                for record in records
                if record.scenario_key == scenario.key
                and record.policy_key == policy.key
            ]
            rows.append(_summarize_one(scenario, policy, selected, config.z_value))
    return tuple(rows)


def _summarize_one(
    scenario: CalibrationScenario,
    policy: CalibrationPolicy,
    records: list[CalibrationRecord],
    z_value: float,
) -> CalibrationSummaryRow:
    released = [record for record in records if record.result.point_estimate is not None]
    raw_errors = np.asarray(
        [
            record.result.raw_point_estimate - record.target_true_effect
            for record in records
            if record.result.raw_point_estimate is not None
        ],
        dtype=float,
    )
    released_errors = np.asarray(
        [record.result.point_estimate - record.target_true_effect for record in released],
        dtype=float,
    )
    interval_records = [
        record
        for record in records
        if np.isfinite(record.result.interval_lower)
        and np.isfinite(record.result.interval_upper)
    ]
    released_interval_records = [
        record
        for record in released
        if np.isfinite(record.result.interval_lower)
        and np.isfinite(record.result.interval_upper)
    ]
    released_covered = [
        record.result.interval_lower
        <= record.target_true_effect
        <= record.result.interval_upper
        for record in released_interval_records
    ]
    overall_covered = [
        record.result.interval_lower
        <= record.target_true_effect
        <= record.result.interval_upper
        for record in interval_records
    ]
    release_rate = len(released) / len(records)
    release_ci_lower, release_ci_upper = wilson_interval(
        len(released),
        len(records),
        z_value,
    )
    by_seed = [
        [record for record in records if record.seed_batch == seed_batch]
        for seed_batch in sorted({record.seed_batch for record in records})
    ]
    seed_release = [
        sum(record.result.point_estimate is not None for record in batch) / len(batch)
        for batch in by_seed
    ]
    seed_coverage = [
        float(
            np.mean(
                [
                    record.result.interval_lower
                    <= record.target_true_effect
                    <= record.result.interval_upper
                    for record in batch
                    if record.result.point_estimate is not None
                    and np.isfinite(record.result.interval_lower)
                    and np.isfinite(record.result.interval_upper)
                ]
            )
        )
        for batch in by_seed
        if any(record.result.point_estimate is not None for record in batch)
    ]
    finite_radii = [
        record.result.certificate.radius
        for record in records
        if np.isfinite(record.result.certificate.radius)
    ]
    released_above_tolerance = [
        record.result.certificate.radius > record.scientific_tolerance
        for record in released
    ]
    return CalibrationSummaryRow(
        scenario_key=scenario.key,
        scenario_label=scenario.label,
        policy_key=policy.key,
        repetitions=len(records),
        seed_batches=len(by_seed),
        released_repetitions=len(released),
        release_rate=release_rate,
        release_ci_lower=release_ci_lower,
        release_ci_upper=release_ci_upper,
        mean_raw_mae=float(np.mean(np.abs(raw_errors))) if raw_errors.size else None,
        released_mae=(
            float(np.mean(np.abs(released_errors))) if released_errors.size else None
        ),
        released_interval_coverage=(
            float(np.mean(released_covered)) if released_covered else None
        ),
        released_interval_uncovered_rate=(
            float(1.0 - np.mean(released_covered)) if released_covered else None
        ),
        released_above_tolerance_rate=(
            float(np.mean(released_above_tolerance))
            if released_above_tolerance
            else None
        ),
        overall_interval_coverage=(
            float(np.mean(overall_covered)) if overall_covered else None
        ),
        mean_certificate_radius=(
            float(np.mean(finite_radii)) if finite_radii else None
        ),
        between_seed_release_sd=(
            float(np.std(seed_release, ddof=1)) if len(seed_release) > 1 else None
        ),
        between_seed_released_coverage_sd=(
            float(np.std(seed_coverage, ddof=1)) if len(seed_coverage) > 1 else None
        ),
    )
