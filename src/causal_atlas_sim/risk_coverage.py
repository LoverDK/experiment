"""Risk--coverage evaluation for the rejectable synthetic estimator.

The curve is computed from one shared set of target draws.  A target is
published when the already-computed certificate radius is below a supplied
scientific threshold; conditional MAE is then reported only on published
targets.  The no-rejection point is the same draw set at acceptance one.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .methods import AtlasConfig, fit_causal_atlas


@dataclass(frozen=True)
class RiskCoverageConfig:
    """Fixed multi-seed protocol for the risk--coverage frontier."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260821, 20260822, 20260823)
    thresholds: tuple[float, ...] = (0.75, 1.00, 1.25, 1.50, 1.65, 2.00, 2.50, 3.00)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=lambda: AtlasConfig(scientific_tolerance=float("inf")))

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2 or not self.base_seeds:
            raise ValueError("repetitions and base_seeds must be nonempty.")
        if not self.thresholds or any(threshold < 0.0 for threshold in self.thresholds):
            raise ValueError("thresholds must be nonnegative and nonempty.")
        if tuple(sorted(set(self.thresholds))) != self.thresholds:
            raise ValueError("thresholds must be strictly increasing.")


@dataclass(frozen=True)
class RiskCoverageRow:
    threshold: float
    acceptance_rate: float
    accepted_count: int
    conditional_mae: float | None
    conditional_rmse: float | None
    conditional_interval_coverage: float | None
    conditional_mean_width: float | None
    unconditional_mae: float
    unconditional_interval_coverage: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskCoverageResult:
    config: RiskCoverageConfig
    rows: tuple[RiskCoverageRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "thresholds": list(self.config.thresholds),
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_risk_coverage_experiment(
    config: RiskCoverageConfig | None = None,
) -> RiskCoverageResult:
    """Run one shared-draw risk--coverage experiment."""

    config = config or RiskCoverageConfig()
    errors: list[float] = []
    covered: list[bool] = []
    widths: list[float] = []
    radii: list[float] = []
    for base_seed in config.base_seeds:
        sequences = np.random.SeedSequence(base_seed).spawn(config.repetitions_per_seed)
        for sequence in sequences:
            seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
            generated = generate_minimal_archive(config.dgp_config, seed=seed)
            result = fit_causal_atlas(
                generated.archive,
                generated.target,
                replace(config.atlas_config, scientific_tolerance=float("inf")),
            )
            if result.raw_point_estimate is None:
                continue
            errors.append(abs(result.raw_point_estimate - generated.target.true_effect))
            covered.append(
                result.interval_lower
                <= generated.target.true_effect
                <= result.interval_upper
            )
            widths.append(result.interval_upper - result.interval_lower)
            radii.append(result.certificate.radius)

    error_array = np.asarray(errors, dtype=float)
    covered_array = np.asarray(covered, dtype=bool)
    rows: list[RiskCoverageRow] = []
    for threshold in config.thresholds:
        accepted = np.asarray(radii, dtype=float) <= threshold + 1e-12
        accepted_errors = error_array[accepted]
        accepted_covered = covered_array[accepted]
        accepted_widths = np.asarray(widths, dtype=float)[accepted]
        rows.append(
            RiskCoverageRow(
                threshold=float(threshold),
                acceptance_rate=float(np.mean(accepted)),
                accepted_count=int(np.sum(accepted)),
                conditional_mae=(float(np.mean(accepted_errors)) if accepted_errors.size else None),
                conditional_rmse=(float(np.sqrt(np.mean(accepted_errors**2))) if accepted_errors.size else None),
                conditional_interval_coverage=(float(np.mean(accepted_covered)) if accepted_covered.size else None),
                conditional_mean_width=(float(np.mean(accepted_widths)) if accepted_widths.size else None),
                unconditional_mae=float(np.mean(error_array)),
                unconditional_interval_coverage=float(np.mean(covered_array)),
            )
        )
    # The endpoint is explicit rather than silently equating a finite threshold
    # with full publication.
    rows.append(
        RiskCoverageRow(
            threshold=float("inf"),
            acceptance_rate=1.0,
            accepted_count=len(error_array),
            conditional_mae=float(np.mean(error_array)),
            conditional_rmse=float(np.sqrt(np.mean(error_array**2))),
            conditional_interval_coverage=float(np.mean(covered_array)),
            conditional_mean_width=float(np.mean(widths)),
            unconditional_mae=float(np.mean(error_array)),
            unconditional_interval_coverage=float(np.mean(covered_array)),
        )
    )
    return RiskCoverageResult(config=config, rows=tuple(rows))
