"""Target-level synthetic diagnostics for certificates and paper benchmarks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .evaluation_baselines import fit_oracle_latent_support
from .methods import (
    AtlasConfig,
    AtlasResult,
    fit_causal_atlas,
    fit_global_mean,
    fit_nearest_semantic_neighbor,
    fit_semantic_forced_composition,
    retrieve_semantic_candidates,
)


BENCHMARK_METHODS = (
    "atlas",
    "atlas_no_rejection",
    "semantic_forced",
    "nearest_semantic",
    "global_mean",
    "oracle_latent_support",
)


@dataclass(frozen=True)
class CertificateDiagnosticsConfig:
    """Shared-target protocol for the certificate/error comparison."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260811, 20260812, 20260813)
    semantic_dimensions: tuple[int, ...] = (0, 1)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2 or not self.base_seeds:
            raise ValueError("The diagnostic protocol needs repetitions and base seeds.")
        if not self.semantic_dimensions:
            raise ValueError("semantic_dimensions cannot be empty.")


@dataclass(frozen=True)
class CertificateDiagnosticRecord:
    seed_batch: int
    replicate: int
    seed: int
    target_s1: float
    target_s2: float
    target_hidden_moderator: float
    target_q: float
    nearest_semantic_s1: float
    nearest_semantic_s2: float
    nearest_semantic_hidden_moderator: float
    nearest_semantic_q: float
    atlas_accepted: bool
    scientific_tolerance: float
    certificate_radius: float
    representation_term: float
    curvature_term: float
    hidden_moderator_term: float
    bias_term: float
    statistical_term: float
    interval_covered: bool
    atlas_absolute_error: float
    atlas_no_rejection_absolute_error: float
    semantic_forced_absolute_error: float
    nearest_semantic_absolute_error: float
    global_mean_absolute_error: float
    oracle_latent_support_absolute_error: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SyntheticBenchmarkRow:
    method: str
    target_evaluations: int
    seed_batches: int
    released_evaluations: int
    release_rate: float
    mae: float | None
    rmse: float | None
    sign_accuracy: float | None
    interval_coverage: float | None
    mean_interval_width: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificateDiagnosticsResult:
    config: CertificateDiagnosticsConfig
    records: tuple[CertificateDiagnosticRecord, ...]
    benchmark_rows: tuple[SyntheticBenchmarkRow, ...]
    spearman_correlation: float
    error_exceeds_certificate_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "semantic_dimensions": list(self.config.semantic_dimensions),
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
            },
            "diagnostics": {
                "spearman_certificate_vs_absolute_error": self.spearman_correlation,
                "error_exceeds_certificate_rate": self.error_exceeds_certificate_rate,
                "comparison_note": (
                    "The plotted realized error and the finite-sample certificate are "
                    "reported as an empirical diagnostic; the exceedance rate is not "
                    "named a theorem violation without an event-by-event equivalence proof."
                ),
            },
            "oracle_scope": (
                "oracle_latent_support replaces public r(e) with simulated m(e) only "
                "for evaluation and is never available to deployment, acceptance, or bridge selection"
            ),
            "benchmark_rows": [row.as_dict() for row in self.benchmark_rows],
        }


@dataclass(frozen=True)
class _MethodEvaluation:
    method: str
    seed_batch: int
    truth: float
    estimate: float
    released: bool
    interval_lower: float
    interval_upper: float


def run_certificate_diagnostics(
    config: CertificateDiagnosticsConfig | None = None,
) -> CertificateDiagnosticsResult:
    """Generate target-level certificate records and a six-method benchmark."""

    config = config or CertificateDiagnosticsConfig()
    records: list[CertificateDiagnosticRecord] = []
    evaluations: list[_MethodEvaluation] = []
    atlas_config = replace(config.atlas_config, representation_dimensions=None)
    semantic_config = replace(
        config.atlas_config,
        representation_dimensions=config.semantic_dimensions,
    )
    for seed_batch, base_seed in enumerate(config.base_seeds):
        sequences = np.random.SeedSequence(base_seed).spawn(
            config.repetitions_per_seed
        )
        for replicate, sequence in enumerate(sequences):
            seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
            generated = generate_minimal_archive(config.dgp_config, seed=seed)
            atlas = fit_causal_atlas(
                generated.archive,
                generated.target,
                atlas_config,
            )
            semantic = fit_semantic_forced_composition(
                generated.archive,
                generated.target,
                semantic_config,
            )
            nearest = fit_nearest_semantic_neighbor(
                generated.archive,
                generated.target,
                semantic_config,
            )
            global_mean = fit_global_mean(
                generated.archive,
                generated.target,
                semantic_config,
            )
            oracle = fit_oracle_latent_support(
                generated.archive,
                generated.target,
                atlas_config,
            )
            method_results = {
                "atlas": atlas,
                "atlas_no_rejection": atlas,
                "semantic_forced": semantic,
                "nearest_semantic": nearest,
                "global_mean": global_mean,
                "oracle_latent_support": oracle,
            }
            truth = generated.target.true_effect
            for method, result in method_results.items():
                if result.raw_point_estimate is None:
                    raise RuntimeError(f"No raw estimate for diagnostic method {method}.")
                evaluations.append(
                    _MethodEvaluation(
                        method=method,
                        seed_batch=seed_batch,
                        truth=truth,
                        estimate=result.raw_point_estimate,
                        released=atlas.accepted if method == "atlas" else True,
                        interval_lower=result.interval_lower,
                        interval_upper=result.interval_upper,
                    )
                )
            nearest_index = retrieve_semantic_candidates(
                generated.archive,
                generated.target,
                config=replace(semantic_config, max_candidates=1),
            )[0]
            nearest_source = generated.archive[nearest_index].mechanism
            atlas_estimate = float(atlas.raw_point_estimate)
            records.append(
                CertificateDiagnosticRecord(
                    seed_batch=seed_batch,
                    replicate=replicate,
                    seed=seed,
                    target_s1=generated.target.mechanism.s1,
                    target_s2=generated.target.mechanism.s2,
                    target_hidden_moderator=generated.target.mechanism.h,
                    target_q=generated.target.mechanism.q,
                    nearest_semantic_s1=nearest_source.s1,
                    nearest_semantic_s2=nearest_source.s2,
                    nearest_semantic_hidden_moderator=nearest_source.h,
                    nearest_semantic_q=nearest_source.q,
                    atlas_accepted=atlas.accepted,
                    scientific_tolerance=atlas_config.scientific_tolerance,
                    certificate_radius=atlas.certificate.radius,
                    representation_term=atlas.certificate.representation_term,
                    curvature_term=atlas.certificate.curvature_term,
                    hidden_moderator_term=atlas.certificate.hidden_moderator_term,
                    bias_term=atlas.certificate.bias_term,
                    statistical_term=atlas.certificate.statistical_term,
                    interval_covered=(
                        atlas.interval_lower <= truth <= atlas.interval_upper
                    ),
                    atlas_absolute_error=abs(atlas_estimate - truth),
                    atlas_no_rejection_absolute_error=abs(atlas_estimate - truth),
                    semantic_forced_absolute_error=abs(
                        float(semantic.raw_point_estimate) - truth
                    ),
                    nearest_semantic_absolute_error=abs(
                        float(nearest.raw_point_estimate) - truth
                    ),
                    global_mean_absolute_error=abs(
                        float(global_mean.raw_point_estimate) - truth
                    ),
                    oracle_latent_support_absolute_error=abs(
                        float(oracle.raw_point_estimate) - truth
                    ),
                )
            )
    radii = np.asarray([record.certificate_radius for record in records])
    errors = np.asarray([record.atlas_absolute_error for record in records])
    return CertificateDiagnosticsResult(
        config=config,
        records=tuple(records),
        benchmark_rows=tuple(
            _summarize_method(method, evaluations, len(config.base_seeds))
            for method in BENCHMARK_METHODS
        ),
        spearman_correlation=_spearman(radii, errors),
        error_exceeds_certificate_rate=float(np.mean(errors > radii)),
    )


def _summarize_method(
    method: str,
    evaluations: list[_MethodEvaluation],
    seed_batches: int,
) -> SyntheticBenchmarkRow:
    all_rows = [item for item in evaluations if item.method == method]
    released = [item for item in all_rows if item.released]
    if not released:
        return SyntheticBenchmarkRow(
            method=method,
            target_evaluations=len(all_rows),
            seed_batches=seed_batches,
            released_evaluations=0,
            release_rate=0.0,
            mae=None,
            rmse=None,
            sign_accuracy=None,
            interval_coverage=None,
            mean_interval_width=None,
        )
    errors = np.asarray([item.estimate - item.truth for item in released])
    coverage = [
        item.interval_lower <= item.truth <= item.interval_upper
        for item in released
    ]
    widths = [item.interval_upper - item.interval_lower for item in released]
    return SyntheticBenchmarkRow(
        method=method,
        target_evaluations=len(all_rows),
        seed_batches=seed_batches,
        released_evaluations=len(released),
        release_rate=len(released) / len(all_rows),
        mae=float(np.mean(np.abs(errors))),
        rmse=float(np.sqrt(np.mean(errors**2))),
        sign_accuracy=float(
            np.mean(
                [np.sign(item.estimate) == np.sign(item.truth) for item in released]
            )
        ),
        interval_coverage=float(np.mean(coverage)),
        mean_interval_width=float(np.mean(widths)),
    )


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Return Spearman correlation without requiring SciPy."""

    x_ranks = _average_ranks(np.asarray(x, dtype=float))
    y_ranks = _average_ranks(np.asarray(y, dtype=float))
    return float(np.corrcoef(x_ranks, y_ranks)[0, 1])


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    start = 0
    while start < values.size:
        end = start + 1
        while end < values.size and values[order[end]] == values[order[start]]:
            end += 1
        ranks[order[start:end]] = (start + end - 1) / 2.0
        start = end
    return ranks
