"""Fair Monte Carlo comparison of Causal ATLAS and transparent baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .methods import (
    METHODS,
    AtlasConfig,
    AtlasResult,
    fit_method,
)


@dataclass(frozen=True)
class MethodComparisonConfig:
    """Controls a comparison with the same DGP draws for every method."""

    repetitions: int = 200
    base_seed: int = 20260805
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    methods: tuple[str, ...] = METHODS

    def __post_init__(self) -> None:
        if self.repetitions < 2:
            raise ValueError("At least two repetitions are required.")
        unknown = set(self.methods) - set(METHODS)
        if unknown:
            raise ValueError(f"Unknown comparison methods: {sorted(unknown)}")
        if not self.methods:
            raise ValueError("At least one method must be compared.")


@dataclass(frozen=True)
class MethodComparisonRecord:
    """One shared synthetic data draw and all method outputs on it."""

    replicate: int
    seed: int
    target_true_effect: float
    results: dict[str, AtlasResult]


@dataclass(frozen=True)
class MethodComparisonResult:
    """Complete repeated comparison and aggregate metrics."""

    config: MethodComparisonConfig
    records: tuple[MethodComparisonRecord, ...]

    def summary(self) -> dict[str, dict[str, Any]]:
        return {method: _summarize_method(self.records, method) for method in self.config.methods}

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions": self.config.repetitions,
                "base_seed": self.config.base_seed,
                "methods": list(self.config.methods),
                "scientific_tolerance": self.config.atlas_config.scientific_tolerance,
            },
            "summary": self.summary(),
        }


def run_method_comparison(
    config: MethodComparisonConfig | None = None,
) -> MethodComparisonResult:
    """Run all methods on exactly the same independent DGP repetitions."""

    config = config or MethodComparisonConfig()
    seed_sequences = np.random.SeedSequence(config.base_seed).spawn(config.repetitions)
    records: list[MethodComparisonRecord] = []
    for replicate, sequence in enumerate(seed_sequences):
        seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
        generated = generate_minimal_archive(config.dgp_config, seed=seed)
        results = {
            method: fit_method(method, generated.archive, generated.target, config.atlas_config)
            for method in config.methods
        }
        records.append(
            MethodComparisonRecord(
                replicate=replicate,
                seed=seed,
                target_true_effect=generated.target.true_effect,
                results=results,
            )
        )
    return MethodComparisonResult(config=config, records=tuple(records))


def _mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def _summarize_method(
    records: tuple[MethodComparisonRecord, ...],
    method: str,
) -> dict[str, Any]:
    method_results = [record.results[method] for record in records]
    accepted = [result for result in method_results if result.point_estimate is not None]
    point_errors = [
        float(result.point_estimate - record.target_true_effect)
        for record, result in zip(records, method_results, strict=True)
        if result.point_estimate is not None
    ]
    interval_results = [
        (record.target_true_effect, result)
        for record, result in zip(records, method_results, strict=True)
        if np.isfinite(result.interval_lower) and np.isfinite(result.interval_upper)
    ]
    widths = [result.interval_upper - result.interval_lower for _, result in interval_results]
    coverage = [
        lower <= truth <= upper
        for truth, result in interval_results
        for lower, upper in [(result.interval_lower, result.interval_upper)]
    ]
    signed_errors = np.asarray(point_errors, dtype=float)
    sign_accuracy = (
        float(
            np.mean(
                [
                    np.sign(result.point_estimate) == np.sign(record.target_true_effect)
                    for record, result in zip(records, method_results, strict=True)
                    if result.point_estimate is not None
                ]
            )
        )
        if accepted
        else None
    )
    return {
        "repetitions": len(records),
        "accepted_repetitions": len(accepted),
        "acceptance_rate": float(np.mean([result.accepted for result in method_results])),
        "rejection_rate": float(np.mean([result.rejected for result in method_results])),
        "accepted_mae": _mean_or_none([abs(error) for error in point_errors]),
        "accepted_rmse": (
            float(np.sqrt(np.mean(signed_errors**2))) if point_errors else None
        ),
        "accepted_bias": _mean_or_none(point_errors),
        "accepted_sign_accuracy": sign_accuracy,
        "interval_coverage": float(np.mean(coverage)) if coverage else None,
        "mean_interval_width": _mean_or_none(widths),
        "mean_certificate_radius": _mean_or_none(
            [result.certificate.radius for result in method_results if np.isfinite(result.certificate.radius)]
        ),
        "mean_representation_term": _mean_or_none(
            [
                result.certificate.representation_term
                for result in method_results
                if np.isfinite(result.certificate.representation_term)
            ]
        ),
        "mean_curvature_term": _mean_or_none(
            [
                result.certificate.curvature_term
                for result in method_results
                if np.isfinite(result.certificate.curvature_term)
            ]
        ),
        "mean_hidden_moderator_term": _mean_or_none(
            [
                result.certificate.hidden_moderator_term
                for result in method_results
                if np.isfinite(result.certificate.hidden_moderator_term)
            ]
        ),
    }
