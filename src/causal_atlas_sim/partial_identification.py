"""Partial identification after failed Causal ATLAS composition.

The interval follows Theorem 5.4: construct valid Theorem 5.1 intervals
for a finite family of design-compatible weights, allocate the overall
failure probability across that family, and intersect the intervals.
True mechanisms and effects are used only by the experiment evaluation
helpers, never by the partial-identification method.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Sequence

import numpy as np

from .dgp import (
    EFFECT_ABSOLUTE_BOUND,
    ExperimentData,
    SimulationConfig,
    generate_minimal_archive,
)
from .formal_experiment import wilson_interval
from .methods import (
    AtlasConfig,
    AtlasResult,
    _project_to_simplex,
    compute_certificate,
    design_compatible,
    filter_design_compatible_candidates,
    fit_causal_atlas,
    optimize_support_weights,
    retrieve_semantic_candidates,
)


@dataclass(frozen=True)
class PartialIdentificationInterval:
    """Intersection of simultaneously certified composition intervals."""

    weight_labels: tuple[str, ...]
    weights: tuple[np.ndarray, ...]
    centers: tuple[float, ...]
    radii: tuple[float, ...]
    interval_lower: float
    interval_upper: float
    total_zeta: float
    component_zeta: float

    @property
    def nonempty(self) -> bool:
        return self.interval_lower <= self.interval_upper

    @property
    def width(self) -> float | None:
        if not self.nonempty:
            return None
        return self.interval_upper - self.interval_lower

    @property
    def reference_width(self) -> float:
        """Width of the support-optimized component at the allocated level."""

        return 2.0 * self.radii[0]

    def contains(self, value: float) -> bool:
        return self.nonempty and self.interval_lower <= value <= self.interval_upper


@dataclass(frozen=True)
class RejectOrIdentifyResult:
    """Point-release decision plus the fallback partial-identification set."""

    atlas_result: AtlasResult
    partial_interval: PartialIdentificationInterval | None


def fit_reject_or_identify(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
    *,
    max_singletons: int = 4,
) -> RejectOrIdentifyResult:
    """Fit ATLAS and construct the Theorem 5.4 fallback interval."""

    config = config or AtlasConfig()
    if max_singletons < 1:
        raise ValueError("max_singletons must be positive.")
    # Local import avoids a module cycle: Algorithm 1 uses the interval
    # constructor below, while this compatibility wrapper uses its dispatcher.
    from .algorithm1 import Algorithm1Config, run_algorithm1

    algorithm_result = run_algorithm1(
        archive,
        target,
        config=Algorithm1Config(
            atlas_config=config,
            max_singletons=max_singletons,
        ),
    )
    return RejectOrIdentifyResult(
        atlas_result=algorithm_result.atlas_result,
        partial_interval=algorithm_result.partial_interval,
    )


def construct_partial_identification_interval(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
    *,
    max_singletons: int = 4,
) -> PartialIdentificationInterval:
    """Construct the Theorem 5.4 interval for pre-debiased archive objects."""

    config = config or AtlasConfig()
    if max_singletons < 1:
        raise ValueError("max_singletons must be positive.")
    weight_labels, weights = _weight_family(
        archive,
        target,
        config,
        max_singletons=max_singletons,
    )
    component_zeta = config.zeta / len(weights)
    certificate_config = replace(config, zeta=component_zeta)
    centers: list[float] = []
    radii: list[float] = []
    lower_bounds: list[float] = []
    upper_bounds: list[float] = []
    for weights_value in weights:
        certificate = compute_certificate(
            archive,
            target,
            weights_value,
            certificate_config,
        )
        center = float(
            sum(
                weight * experiment.estimated_effect
                for weight, experiment in zip(
                    weights_value, archive, strict=True
                )
            )
        )
        centers.append(center)
        radii.append(certificate.radius)
        lower_bounds.append(center - certificate.radius)
        upper_bounds.append(center + certificate.radius)
    return PartialIdentificationInterval(
        weight_labels=weight_labels,
        weights=weights,
        centers=tuple(centers),
        radii=tuple(radii),
        interval_lower=max(lower_bounds),
        interval_upper=min(upper_bounds),
        total_zeta=config.zeta,
        component_zeta=component_zeta,
    )


def _weight_family(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig,
    *,
    max_singletons: int,
) -> tuple[tuple[str, ...], tuple[np.ndarray, ...]]:
    candidates = filter_design_compatible_candidates(
        archive,
        target,
        retrieve_semantic_candidates(archive, target, config=config),
    )
    compatible = tuple(
        index
        for index, experiment in enumerate(archive)
        if design_compatible(experiment, target)
    )
    if not candidates or not compatible:
        raise ValueError("Partial identification needs design-compatible archive studies.")
    optimized, _ = optimize_support_weights(
        archive,
        target,
        compatible,
        config,
    )
    uniform = np.zeros(len(archive), dtype=float)
    uniform[list(compatible)] = 1.0 / len(compatible)
    family: list[tuple[str, np.ndarray]] = [
        ("support_optimized", optimized),
        ("compatible_uniform", uniform),
    ]
    for rank, index in enumerate(candidates[:max_singletons], start=1):
        singleton = np.zeros(len(archive), dtype=float)
        singleton[index] = 1.0
        family.append((f"semantic_neighbor_{rank}", singleton))

    unique: list[tuple[str, np.ndarray]] = []
    for label, weights in family:
        if not any(np.allclose(weights, existing) for _, existing in unique):
            unique.append((label, weights))
    return (
        tuple(label for label, _ in unique),
        tuple(weights.copy() for _, weights in unique),
    )


def oracle_hull_distance(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    *,
    max_iterations: int = 2000,
    tolerance: float = 1e-12,
) -> float:
    """Evaluate target distance to the true design-compatible mechanism hull."""

    compatible = [
        experiment
        for experiment in archive
        if design_compatible(experiment, target)
    ]
    if not compatible:
        raise ValueError("Oracle hull distance needs compatible archive studies.")
    mechanisms = np.vstack(
        [experiment.mechanism.as_array() for experiment in compatible]
    )
    target_mechanism = target.mechanism.as_array()
    weights = np.full(len(compatible), 1.0 / len(compatible))
    spectral_norm = float(np.linalg.norm(mechanisms, ord=2))
    step = 1.0 / max(spectral_norm**2, 1e-12)
    for _ in range(max_iterations):
        residual = weights @ mechanisms - target_mechanism
        gradient = mechanisms @ residual
        proposal = _project_to_simplex(weights - step * gradient)
        if np.linalg.norm(proposal - weights) <= tolerance:
            weights = proposal
            break
        weights = proposal
    return float(np.linalg.norm(weights @ mechanisms - target_mechanism))


@dataclass(frozen=True)
class PartialIdentificationScenario:
    """One target-support scenario for the Theorem 5.4 experiment."""

    key: str
    label: str
    semantic_shift_fraction: float
    scientific_tolerance: float = 1.65

    def __post_init__(self) -> None:
        if not self.key or not self.label:
            raise ValueError("A partial-identification scenario needs a key and label.")
        if not 0.0 <= self.semantic_shift_fraction <= 1.0:
            raise ValueError("semantic_shift_fraction must lie in [0, 1].")
        if self.scientific_tolerance < 0.0:
            raise ValueError("scientific_tolerance must be nonnegative.")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_partial_identification_scenarios(
) -> tuple[PartialIdentificationScenario, ...]:
    """Return supported through severely unsupported target scenarios."""

    return (
        PartialIdentificationScenario("nominal", "nominal support", 0.0),
        PartialIdentificationScenario(
            "moderate_mismatch",
            "moderate semantic mismatch",
            0.25,
        ),
        PartialIdentificationScenario(
            "strong_mismatch",
            "strong semantic mismatch",
            0.60,
        ),
        PartialIdentificationScenario(
            "severe_mismatch",
            "severe semantic mismatch",
            0.80,
        ),
    )


@dataclass(frozen=True)
class PartialIdentificationExperimentConfig:
    """Controls the fixed multi-seed partial-identification experiment."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260911, 20260912, 20260913)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    scenarios: tuple[PartialIdentificationScenario, ...] = field(
        default_factory=default_partial_identification_scenarios
    )
    max_singletons: int = 4
    z_value: float = 1.96

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2:
            raise ValueError("At least two repetitions per seed are required.")
        if not self.base_seeds or not self.scenarios:
            raise ValueError("Seeds and scenarios must be nonempty.")
        if self.max_singletons < 1:
            raise ValueError("max_singletons must be positive.")
        if self.z_value <= 0.0:
            raise ValueError("z_value must be positive.")


@dataclass(frozen=True)
class PartialIdentificationRecord:
    """One reject-or-identify result with oracle-only evaluation metadata."""

    scenario_key: str
    scenario_label: str
    seed_batch: int
    replicate: int
    seed: int
    target_true_effect: float
    oracle_hull_distance: float
    nonidentification_separation: float
    result: RejectOrIdentifyResult


@dataclass(frozen=True)
class PartialIdentificationSummaryRow:
    """Coverage, width, rejection, and support metrics for one scenario."""

    scenario_key: str
    scenario_label: str
    repetitions: int
    seed_batches: int
    rejected_repetitions: int
    rejection_rate: float
    rejection_ci_lower: float
    rejection_ci_upper: float
    partial_id_nonempty_rate: float
    partial_id_coverage: float
    partial_id_coverage_on_rejected: float | None
    mean_partial_id_width: float | None
    mean_partial_id_width_on_rejected: float | None
    mean_reference_width_on_rejected: float | None
    mean_width_reduction_fraction_on_rejected: float | None
    mean_oracle_hull_distance: float
    mean_nonidentification_separation: float
    between_seed_partial_coverage_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PartialIdentificationExperimentResult:
    """All records and summary rows for the Stage 9 experiment."""

    config: PartialIdentificationExperimentConfig
    records: tuple[PartialIdentificationRecord, ...]
    rows: tuple[PartialIdentificationSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
                "scenarios": [scenario.as_dict() for scenario in self.config.scenarios],
                "max_singletons": self.config.max_singletons,
                "z_value": self.config.z_value,
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_partial_identification_experiment(
    config: PartialIdentificationExperimentConfig | None = None,
) -> PartialIdentificationExperimentResult:
    """Run the fixed shared-seed Theorem 5.4 experiment."""

    config = config or PartialIdentificationExperimentConfig()
    records: list[PartialIdentificationRecord] = []
    for scenario in config.scenarios:
        dgp_config = replace(
            config.dgp_config,
            target_shift_fraction=scenario.semantic_shift_fraction,
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
                result = fit_reject_or_identify(
                    generated.archive,
                    generated.target,
                    atlas_config,
                    max_singletons=config.max_singletons,
                )
                distance = oracle_hull_distance(
                    generated.archive,
                    generated.target,
                )
                records.append(
                    PartialIdentificationRecord(
                        scenario_key=scenario.key,
                        scenario_label=scenario.label,
                        seed_batch=seed_batch,
                        replicate=replicate,
                        seed=seed,
                        target_true_effect=generated.target.true_effect,
                        oracle_hull_distance=distance,
                        nonidentification_separation=min(
                            atlas_config.effect_lipschitz_bound * distance,
                            EFFECT_ABSOLUTE_BOUND,
                        ),
                        result=result,
                    )
                )
    return PartialIdentificationExperimentResult(
        config=config,
        records=tuple(records),
        rows=_summarize_records(records, config),
    )


def _summarize_records(
    records: list[PartialIdentificationRecord],
    config: PartialIdentificationExperimentConfig,
) -> tuple[PartialIdentificationSummaryRow, ...]:
    return tuple(
        _summarize_one(
            scenario,
            [
                record
                for record in records
                if record.scenario_key == scenario.key
            ],
            config.z_value,
        )
        for scenario in config.scenarios
    )


def _summarize_one(
    scenario: PartialIdentificationScenario,
    records: list[PartialIdentificationRecord],
    z_value: float,
) -> PartialIdentificationSummaryRow:
    rejected = [
        record for record in records if record.result.atlas_result.rejected
    ]
    partial_records = [
        record
        for record in records
        if record.result.partial_interval is not None
    ]
    nonempty = [
        record
        for record in partial_records
        if record.result.partial_interval is not None
        and record.result.partial_interval.nonempty
    ]
    rejected_nonempty = [
        record
        for record in rejected
        if record.result.partial_interval is not None
        and record.result.partial_interval.nonempty
    ]
    coverage = [
        record.result.partial_interval.contains(record.target_true_effect)
        for record in partial_records
        if record.result.partial_interval is not None
    ]
    rejected_coverage = [
        record.result.partial_interval.contains(record.target_true_effect)
        for record in rejected
        if record.result.partial_interval is not None
    ]
    widths = [
        record.result.partial_interval.width
        for record in nonempty
        if record.result.partial_interval is not None
    ]
    rejected_widths = [
        record.result.partial_interval.width
        for record in rejected_nonempty
        if record.result.partial_interval is not None
    ]
    rejected_reference_widths = [
        record.result.partial_interval.reference_width
        for record in rejected_nonempty
        if record.result.partial_interval is not None
    ]
    reductions = [
        (
            record.result.partial_interval.reference_width
            - record.result.partial_interval.width
        )
        / record.result.partial_interval.reference_width
        for record in rejected_nonempty
        if record.result.partial_interval is not None
    ]
    rejection_ci_lower, rejection_ci_upper = wilson_interval(
        len(rejected),
        len(records),
        z_value,
    )
    by_seed = [
        [record for record in records if record.seed_batch == seed_batch]
        for seed_batch in sorted({record.seed_batch for record in records})
    ]
    seed_coverages = [
        float(
            np.mean(
                [
                    record.result.partial_interval is not None
                    and record.result.partial_interval.contains(
                        record.target_true_effect
                    )
                    for record in batch
                ]
            )
        )
        for batch in by_seed
    ]
    return PartialIdentificationSummaryRow(
        scenario_key=scenario.key,
        scenario_label=scenario.label,
        repetitions=len(records),
        seed_batches=len(by_seed),
        rejected_repetitions=len(rejected),
        rejection_rate=len(rejected) / len(records),
        rejection_ci_lower=rejection_ci_lower,
        rejection_ci_upper=rejection_ci_upper,
        partial_id_nonempty_rate=(
            len(nonempty) / len(partial_records) if partial_records else 0.0
        ),
        partial_id_coverage=(
            float(np.mean(coverage)) if coverage else 0.0
        ),
        partial_id_coverage_on_rejected=(
            float(np.mean(rejected_coverage)) if rejected_coverage else None
        ),
        mean_partial_id_width=(
            float(np.mean(widths)) if widths else None
        ),
        mean_partial_id_width_on_rejected=(
            float(np.mean(rejected_widths)) if rejected_widths else None
        ),
        mean_reference_width_on_rejected=(
            float(np.mean(rejected_reference_widths))
            if rejected_reference_widths
            else None
        ),
        mean_width_reduction_fraction_on_rejected=(
            float(np.mean(reductions)) if reductions else None
        ),
        mean_oracle_hull_distance=float(
            np.mean([record.oracle_hull_distance for record in records])
        ),
        mean_nonidentification_separation=float(
            np.mean(
                [record.nonidentification_separation for record in records]
            )
        ),
        between_seed_partial_coverage_sd=(
            float(np.std(seed_coverages, ddof=1))
            if len(seed_coverages) > 1
            else None
        ),
    )
