"""Monte Carlo repetition and evaluation for the minimal certified DGP.

This module deliberately evaluates only an oracle-support composition.  It is
an infrastructure check for repeated sampling, metrics, and interval logic;
it is not the Causal ATLAS weight-learning method.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import numpy as np

from .dgp import (
    EFFECT_CURVATURE_BOUND,
    GeneratedArchive,
    SimulationConfig,
    generate_minimal_archive,
)


@dataclass(frozen=True)
class MonteCarloConfig:
    """Controls independent repetitions of the certified minimal DGP."""

    repetitions: int = 200
    base_seed: int = 20260805
    z_value: float = 1.96
    dgp_config: SimulationConfig = SimulationConfig()

    def __post_init__(self) -> None:
        if self.repetitions < 2:
            raise ValueError("At least two repetitions are required.")
        if self.z_value <= 0.0:
            raise ValueError("z_value must be positive.")


@dataclass(frozen=True)
class MonteCarloRecord:
    """One repetition's target truth, oracle prediction, and certificates."""

    replicate: int
    seed: int
    target_true_effect: float
    target_direct_estimate: float
    oracle_composition_true_effect: float
    oracle_composition_estimate: float
    oracle_composition_signed_error: float
    oracle_composition_absolute_error: float
    target_direct_absolute_error: float
    sign_correct: bool
    oracle_standard_error: float
    noise_only_interval_lower: float
    noise_only_interval_upper: float
    noise_only_interval_covered: bool
    certified_radius: float
    certified_interval_lower: float
    certified_interval_upper: float
    certified_interval_covered: bool
    curvature_bound: float
    hidden_moderator_certificate: float
    support_residual: float
    curvature_bound_holds: bool


@dataclass(frozen=True)
class MonteCarloResult:
    """All repetition records and scalar summaries used in reports."""

    config: MonteCarloConfig
    records: tuple[MonteCarloRecord, ...]

    def summary(self) -> dict[str, Any]:
        records = self.records
        signed_errors = np.array([record.oracle_composition_signed_error for record in records])
        absolute_errors = np.array([record.oracle_composition_absolute_error for record in records])
        direct_errors = np.array([record.target_direct_absolute_error for record in records])
        noise_coverage = np.array([record.noise_only_interval_covered for record in records])
        certified_coverage = np.array([record.certified_interval_covered for record in records])
        certified_widths = np.array(
            [record.certified_interval_upper - record.certified_interval_lower for record in records]
        )
        noise_widths = np.array(
            [record.noise_only_interval_upper - record.noise_only_interval_lower for record in records]
        )
        return {
            "repetitions": len(records),
            "mean_absolute_error": float(np.mean(absolute_errors)),
            "rmse": float(np.sqrt(np.mean(signed_errors**2))),
            "bias": float(np.mean(signed_errors)),
            "sign_accuracy": float(np.mean([record.sign_correct for record in records])),
            "target_direct_mae": float(np.mean(direct_errors)),
            "noise_only_coverage": float(np.mean(noise_coverage)),
            "certified_coverage": float(np.mean(certified_coverage)),
            "mean_noise_only_interval_width": float(np.mean(noise_widths)),
            "mean_certified_interval_width": float(np.mean(certified_widths)),
            "mean_curvature_bound": float(np.mean([record.curvature_bound for record in records])),
            "mean_hidden_moderator_certificate": float(
                np.mean([record.hidden_moderator_certificate for record in records])
            ),
            "mean_support_residual": float(np.mean([record.support_residual for record in records])),
            "curvature_bound_violation_rate": float(
                np.mean([not record.curvature_bound_holds for record in records])
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions": self.config.repetitions,
                "base_seed": self.config.base_seed,
                "z_value": self.config.z_value,
            },
            "summary": self.summary(),
        }


def run_monte_carlo(config: MonteCarloConfig | None = None) -> MonteCarloResult:
    """Run independent DGP repetitions and evaluate oracle composition."""

    config = config or MonteCarloConfig()
    seed_sequences = np.random.SeedSequence(config.base_seed).spawn(config.repetitions)
    records: list[MonteCarloRecord] = []
    for replicate, sequence in enumerate(seed_sequences):
        seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
        generated = generate_minimal_archive(config.dgp_config, seed=seed)
        records.append(_evaluate_repetition(replicate, seed, generated, config.z_value))
    return MonteCarloResult(config=config, records=tuple(records))


def _evaluate_repetition(
    replicate: int,
    seed: int,
    generated: GeneratedArchive,
    z_value: float,
) -> MonteCarloRecord:
    weights = generated.target_support_weights
    archive_estimates = np.array([experiment.estimated_effect for experiment in generated.archive])
    archive_true_effects = np.array([experiment.true_effect for experiment in generated.archive])
    archive_se = np.array(
        [experiment.standard_error_certificate for experiment in generated.archive], dtype=float
    )
    target_true_effect = generated.target.true_effect
    target_direct_estimate = generated.target.estimated_effect
    oracle_composition_true_effect = float(weights @ archive_true_effects)
    oracle_composition_estimate = float(weights @ archive_estimates)
    oracle_composition_signed_error = oracle_composition_estimate - target_true_effect
    oracle_standard_error = float(np.sqrt(np.sum((weights * archive_se) ** 2)))
    noise_only_radius = z_value * oracle_standard_error
    noise_only_lower = oracle_composition_estimate - noise_only_radius
    noise_only_upper = oracle_composition_estimate + noise_only_radius

    weighted_mechanism = generated.weighted_archive_mechanism()
    curvature_bound = float(
        EFFECT_CURVATURE_BOUND
        / 2.0
        * sum(
            weight * np.linalg.norm(experiment.mechanism.as_array() - weighted_mechanism) ** 2
            for weight, experiment in zip(weights, generated.archive, strict=True)
        )
    )
    hidden_moderator_certificate = generated.hidden_moderator_certificate(weights)
    certified_radius = curvature_bound + hidden_moderator_certificate + noise_only_radius
    certified_lower = oracle_composition_estimate - certified_radius
    certified_upper = oracle_composition_estimate + certified_radius
    curvature_error = abs(oracle_composition_true_effect - target_true_effect)

    return MonteCarloRecord(
        replicate=replicate,
        seed=seed,
        target_true_effect=target_true_effect,
        target_direct_estimate=target_direct_estimate,
        oracle_composition_true_effect=oracle_composition_true_effect,
        oracle_composition_estimate=oracle_composition_estimate,
        oracle_composition_signed_error=oracle_composition_signed_error,
        oracle_composition_absolute_error=abs(oracle_composition_signed_error),
        target_direct_absolute_error=abs(target_direct_estimate - target_true_effect),
        sign_correct=bool(np.sign(oracle_composition_estimate) == np.sign(target_true_effect)),
        oracle_standard_error=oracle_standard_error,
        noise_only_interval_lower=noise_only_lower,
        noise_only_interval_upper=noise_only_upper,
        noise_only_interval_covered=bool(noise_only_lower <= target_true_effect <= noise_only_upper),
        certified_radius=certified_radius,
        certified_interval_lower=certified_lower,
        certified_interval_upper=certified_upper,
        certified_interval_covered=bool(certified_lower <= target_true_effect <= certified_upper),
        curvature_bound=curvature_bound,
        hidden_moderator_certificate=hidden_moderator_certificate,
        support_residual=generated.support_residual(),
        curvature_bound_holds=bool(curvature_error <= curvature_bound + 1e-12),
    )
