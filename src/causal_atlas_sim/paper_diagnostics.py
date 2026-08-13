"""Paper-facing selective-risk and interval-calibration diagnostics.

These diagnostics are deliberately downstream of the core Causal ATLAS method.
They do not change Algorithm 1.  Instead, they expose two quantities that are
important when interpreting a rejectable estimator in a paper:

1. the risk--coverage frontier induced by thresholding the finite-sample
   certificate; and
2. empirical coverage together with interval width across nominal confidence
   levels, comparing the honest Corollary 5.2 interval with a Wald-only
   interval that omits approximation uncertainty.

The target truth and latent mechanism are used only after prediction for
synthetic evaluation.  Thresholding never uses the target outcome or target
truth.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from math import sqrt
from statistics import NormalDist
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .methods import AtlasConfig, fit_causal_atlas


@dataclass(frozen=True)
class PaperDiagnosticsConfig:
    """Fixed protocol for paper-facing diagnostics on the nominal DGP."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260811, 20260812, 20260813)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    tolerance_grid: tuple[float, ...] = (
        0.50,
        0.75,
        1.00,
        1.25,
        1.50,
        1.65,
        1.75,
        2.00,
        2.50,
        3.00,
        5.00,
    )
    confidence_levels: tuple[float, ...] = (0.80, 0.90, 0.95, 0.975)

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2:
            raise ValueError("At least two repetitions per seed are required.")
        if not self.base_seeds:
            raise ValueError("At least one base seed is required.")
        if not self.tolerance_grid:
            raise ValueError("At least one certificate tolerance is required.")
        if any(value < 0.0 for value in self.tolerance_grid):
            raise ValueError("Certificate tolerances must be nonnegative.")
        if tuple(sorted(self.tolerance_grid)) != self.tolerance_grid:
            raise ValueError("tolerance_grid must be sorted in nondecreasing order.")
        if not self.confidence_levels:
            raise ValueError("At least one confidence level is required.")
        if any(not 0.0 < level < 1.0 for level in self.confidence_levels):
            raise ValueError("confidence levels must lie in (0, 1).")


@dataclass(frozen=True)
class DiagnosticRecord:
    """One raw ATLAS prediction before applying a paper-level release threshold."""

    seed_batch: int
    replicate: int
    seed: int
    target_true_effect: float
    raw_point_estimate: float
    certificate_radius: float
    approximation_radius: float
    weighted_standard_error: float

    @property
    def absolute_error(self) -> float:
        return abs(self.raw_point_estimate - self.target_true_effect)


@dataclass(frozen=True)
class RiskCoverageRow:
    """Conditional risk at one prespecified certificate tolerance."""

    certificate_tolerance: float
    repetitions: int
    accepted_repetitions: int
    acceptance_rate: float
    accepted_mae: float | None
    accepted_rmse: float | None
    rejected_mae: float | None
    all_target_mae: float
    mean_accepted_certificate_radius: float | None
    between_seed_acceptance_sd: float | None
    between_seed_accepted_mae_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IntervalCalibrationRow:
    """Coverage and width at one nominal confidence level."""

    confidence_level: float
    repetitions: int
    honest_coverage: float
    honest_mean_width: float
    wald_coverage: float
    wald_mean_width: float
    approximation_width_increment: float
    between_seed_honest_coverage_sd: float | None
    between_seed_wald_coverage_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PaperDiagnosticsResult:
    """Raw records and the two paper-facing diagnostic tables."""

    config: PaperDiagnosticsConfig
    records: tuple[DiagnosticRecord, ...]
    risk_coverage_rows: tuple[RiskCoverageRow, ...]
    interval_calibration_rows: tuple[IntervalCalibrationRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
                "tolerance_grid": list(self.config.tolerance_grid),
                "confidence_levels": list(self.config.confidence_levels),
            },
            "risk_coverage_rows": [
                row.as_dict() for row in self.risk_coverage_rows
            ],
            "interval_calibration_rows": [
                row.as_dict() for row in self.interval_calibration_rows
            ],
        }


def run_paper_diagnostics(
    config: PaperDiagnosticsConfig | None = None,
) -> PaperDiagnosticsResult:
    """Run shared nominal draws and summarize selective risk and calibration."""

    config = config or PaperDiagnosticsConfig()
    records: list[DiagnosticRecord] = []

    # Use a very large tolerance so the core fit always exposes its raw point
    # prediction when design-compatible candidates exist.  Paper-level release
    # thresholds are then applied to the stored certificate without refitting.
    fitting_config = replace(config.atlas_config, scientific_tolerance=1.0e12)

    for seed_batch, base_seed in enumerate(config.base_seeds):
        sequences = np.random.SeedSequence(base_seed).spawn(
            config.repetitions_per_seed
        )
        for replicate, sequence in enumerate(sequences):
            seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
            generated = generate_minimal_archive(config.dgp_config, seed=seed)
            result = fit_causal_atlas(
                generated.archive,
                generated.target,
                fitting_config,
            )
            if result.raw_point_estimate is None:
                continue
            weighted_se = sqrt(
                sum(
                    weight**2 * source.standard_error_certificate**2
                    for weight, source in zip(
                        result.weights, generated.archive, strict=True
                    )
                )
            )
            certificate = result.certificate
            approximation_radius = (
                certificate.representation_term
                + certificate.curvature_term
                + certificate.hidden_moderator_term
                + certificate.bias_term
            )
            records.append(
                DiagnosticRecord(
                    seed_batch=seed_batch,
                    replicate=replicate,
                    seed=seed,
                    target_true_effect=generated.target.true_effect,
                    raw_point_estimate=float(result.raw_point_estimate),
                    certificate_radius=float(certificate.radius),
                    approximation_radius=float(approximation_radius),
                    weighted_standard_error=float(weighted_se),
                )
            )

    if not records:
        raise RuntimeError("Paper diagnostics produced no finite ATLAS predictions.")

    return PaperDiagnosticsResult(
        config=config,
        records=tuple(records),
        risk_coverage_rows=_summarize_risk_coverage(records, config),
        interval_calibration_rows=_summarize_interval_calibration(records, config),
    )


def _summarize_risk_coverage(
    records: list[DiagnosticRecord],
    config: PaperDiagnosticsConfig,
) -> tuple[RiskCoverageRow, ...]:
    all_errors = np.asarray(
        [record.raw_point_estimate - record.target_true_effect for record in records],
        dtype=float,
    )
    all_target_mae = float(np.mean(np.abs(all_errors)))
    rows: list[RiskCoverageRow] = []

    for tolerance in config.tolerance_grid:
        accepted = [
            record for record in records if record.certificate_radius <= tolerance + 1e-12
        ]
        rejected = [
            record for record in records if record.certificate_radius > tolerance + 1e-12
        ]
        accepted_errors = np.asarray(
            [record.raw_point_estimate - record.target_true_effect for record in accepted],
            dtype=float,
        )
        rejected_errors = np.asarray(
            [record.raw_point_estimate - record.target_true_effect for record in rejected],
            dtype=float,
        )
        seed_acceptance: list[float] = []
        seed_mae: list[float] = []
        for seed_batch in sorted({record.seed_batch for record in records}):
            batch = [record for record in records if record.seed_batch == seed_batch]
            batch_accepted = [
                record
                for record in batch
                if record.certificate_radius <= tolerance + 1e-12
            ]
            seed_acceptance.append(len(batch_accepted) / len(batch))
            if batch_accepted:
                seed_mae.append(
                    float(np.mean([record.absolute_error for record in batch_accepted]))
                )
        rows.append(
            RiskCoverageRow(
                certificate_tolerance=float(tolerance),
                repetitions=len(records),
                accepted_repetitions=len(accepted),
                acceptance_rate=len(accepted) / len(records),
                accepted_mae=(
                    float(np.mean(np.abs(accepted_errors)))
                    if accepted_errors.size
                    else None
                ),
                accepted_rmse=(
                    float(np.sqrt(np.mean(accepted_errors**2)))
                    if accepted_errors.size
                    else None
                ),
                rejected_mae=(
                    float(np.mean(np.abs(rejected_errors)))
                    if rejected_errors.size
                    else None
                ),
                all_target_mae=all_target_mae,
                mean_accepted_certificate_radius=(
                    float(np.mean([record.certificate_radius for record in accepted]))
                    if accepted
                    else None
                ),
                between_seed_acceptance_sd=(
                    float(np.std(seed_acceptance, ddof=1))
                    if len(seed_acceptance) > 1
                    else None
                ),
                between_seed_accepted_mae_sd=(
                    float(np.std(seed_mae, ddof=1)) if len(seed_mae) > 1 else None
                ),
            )
        )
    return tuple(rows)


def _summarize_interval_calibration(
    records: list[DiagnosticRecord],
    config: PaperDiagnosticsConfig,
) -> tuple[IntervalCalibrationRow, ...]:
    rows: list[IntervalCalibrationRow] = []
    for level in config.confidence_levels:
        z_value = NormalDist().inv_cdf(0.5 + level / 2.0)
        honest_covered: list[bool] = []
        wald_covered: list[bool] = []
        honest_widths: list[float] = []
        wald_widths: list[float] = []
        seed_honest: list[float] = []
        seed_wald: list[float] = []

        for record in records:
            wald_radius = z_value * record.weighted_standard_error
            honest_radius = record.approximation_radius + wald_radius
            error = abs(record.raw_point_estimate - record.target_true_effect)
            honest_covered.append(error <= honest_radius + 1e-12)
            wald_covered.append(error <= wald_radius + 1e-12)
            honest_widths.append(2.0 * honest_radius)
            wald_widths.append(2.0 * wald_radius)

        for seed_batch in sorted({record.seed_batch for record in records}):
            batch = [record for record in records if record.seed_batch == seed_batch]
            batch_honest = []
            batch_wald = []
            for record in batch:
                wald_radius = z_value * record.weighted_standard_error
                honest_radius = record.approximation_radius + wald_radius
                error = abs(record.raw_point_estimate - record.target_true_effect)
                batch_honest.append(error <= honest_radius + 1e-12)
                batch_wald.append(error <= wald_radius + 1e-12)
            seed_honest.append(float(np.mean(batch_honest)))
            seed_wald.append(float(np.mean(batch_wald)))

        honest_mean_width = float(np.mean(honest_widths))
        wald_mean_width = float(np.mean(wald_widths))
        rows.append(
            IntervalCalibrationRow(
                confidence_level=float(level),
                repetitions=len(records),
                honest_coverage=float(np.mean(honest_covered)),
                honest_mean_width=honest_mean_width,
                wald_coverage=float(np.mean(wald_covered)),
                wald_mean_width=wald_mean_width,
                approximation_width_increment=honest_mean_width - wald_mean_width,
                between_seed_honest_coverage_sd=(
                    float(np.std(seed_honest, ddof=1))
                    if len(seed_honest) > 1
                    else None
                ),
                between_seed_wald_coverage_sd=(
                    float(np.std(seed_wald, ddof=1))
                    if len(seed_wald) > 1
                    else None
                ),
            )
        )
    return tuple(rows)
