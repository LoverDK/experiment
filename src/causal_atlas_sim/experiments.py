"""Main one-factor-at-a-time simulation protocol and result table helpers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .comparison import MethodComparisonConfig, run_method_comparison
from .dgp import SimulationConfig
from .methods import METHODS, AtlasConfig


@dataclass(frozen=True)
class SweepDefinition:
    """One controlled factor and its fixed levels."""

    key: str
    label: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.key or not self.values:
            raise ValueError("A sweep needs a key and at least one level.")
        if len(set(self.values)) != len(self.values):
            raise ValueError("Sweep levels must be unique.")


def default_sweeps() -> tuple[SweepDefinition, ...]:
    """Return the preregistered four-factor screening grid."""

    return (
        SweepDefinition(
            "semantic_shift_fraction",
            "semantic mismatch fraction",
            (0.0, 0.10, 0.25),
        ),
        SweepDefinition(
            "moderator_sensitivity_radius",
            "hidden moderator sensitivity radius",
            (0.20, 0.40, 0.60),
        ),
        SweepDefinition(
            "sample_size",
            "units per experiment",
            (100.0, 400.0, 1000.0),
        ),
        SweepDefinition(
            "scientific_tolerance",
            "scientific tolerance",
            (1.25, 1.65, 2.05),
        ),
    )


@dataclass(frozen=True)
class MainExperimentConfig:
    """Configuration for the fixed-seed main experiment protocol."""

    repetitions: int = 200
    base_seed: int = 20260806
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)
    sweeps: tuple[SweepDefinition, ...] = field(default_factory=default_sweeps)
    methods: tuple[str, ...] = METHODS

    def __post_init__(self) -> None:
        if self.repetitions < 2:
            raise ValueError("At least two repetitions are required.")
        if not self.sweeps:
            raise ValueError("At least one sweep is required.")


@dataclass(frozen=True)
class ExperimentSummaryRow:
    """One method x one factor level row for CSV and plotting."""

    sweep_key: str
    sweep_label: str
    level: float
    method: str
    repetitions: int
    accepted_repetitions: int
    acceptance_rate: float
    rejection_rate: float
    accepted_mae: float | None
    accepted_rmse: float | None
    accepted_bias: float | None
    accepted_sign_accuracy: float | None
    interval_coverage: float | None
    mean_interval_width: float | None
    mean_certificate_radius: float | None
    mean_representation_term: float | None
    mean_curvature_term: float | None
    mean_hidden_moderator_term: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sweep_key": self.sweep_key,
            "sweep_label": self.sweep_label,
            "level": self.level,
            "method": self.method,
            "repetitions": self.repetitions,
            "accepted_repetitions": self.accepted_repetitions,
            "acceptance_rate": self.acceptance_rate,
            "rejection_rate": self.rejection_rate,
            "accepted_mae": self.accepted_mae,
            "accepted_rmse": self.accepted_rmse,
            "accepted_bias": self.accepted_bias,
            "accepted_sign_accuracy": self.accepted_sign_accuracy,
            "interval_coverage": self.interval_coverage,
            "mean_interval_width": self.mean_interval_width,
            "mean_certificate_radius": self.mean_certificate_radius,
            "mean_representation_term": self.mean_representation_term,
            "mean_curvature_term": self.mean_curvature_term,
            "mean_hidden_moderator_term": self.mean_hidden_moderator_term,
        }


@dataclass(frozen=True)
class MainExperimentResult:
    """All factor-level comparisons and their long-form summary table."""

    config: MainExperimentConfig
    rows: tuple[ExperimentSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions": self.config.repetitions,
                "base_seed": self.config.base_seed,
                "methods": list(self.config.methods),
                "sweeps": [
                    {"key": sweep.key, "label": sweep.label, "values": list(sweep.values)}
                    for sweep in self.config.sweeps
                ],
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_main_experiment(
    config: MainExperimentConfig | None = None,
) -> MainExperimentResult:
    """Run every factor level with shared seeds across methods and levels."""

    config = config or MainExperimentConfig()
    rows: list[ExperimentSummaryRow] = []
    for sweep_index, sweep in enumerate(config.sweeps):
        for level in sweep.values:
            dgp_config, atlas_config = _configs_for_level(config, sweep.key, level)
            comparison = run_method_comparison(
                MethodComparisonConfig(
                    repetitions=config.repetitions,
                    base_seed=config.base_seed + sweep_index,
                    dgp_config=dgp_config,
                    atlas_config=atlas_config,
                    methods=config.methods,
                )
            )
            summaries = comparison.summary()
            rows.extend(
                _summary_rows(sweep, level, summaries, config.methods)
            )
    return MainExperimentResult(config=config, rows=tuple(rows))


def _configs_for_level(
    config: MainExperimentConfig,
    key: str,
    level: float,
) -> tuple[SimulationConfig, AtlasConfig]:
    dgp_config = config.dgp_config
    atlas_config = config.atlas_config
    if key == "semantic_shift_fraction":
        dgp_config = replace(dgp_config, target_shift_fraction=float(level))
    elif key == "moderator_sensitivity_radius":
        dgp_config = replace(dgp_config, moderator_sensitivity_radius=float(level))
    elif key == "sample_size":
        sample_size = int(level)
        dgp_config = replace(
            dgp_config,
            n_units_per_experiment=sample_size,
            n_units_target=sample_size,
        )
    elif key == "scientific_tolerance":
        atlas_config = replace(atlas_config, scientific_tolerance=float(level))
    else:
        raise ValueError(f"Unsupported sweep key: {key}")
    return dgp_config, atlas_config


def _summary_rows(
    sweep: SweepDefinition,
    level: float,
    summaries: dict[str, dict[str, Any]],
    methods: tuple[str, ...],
) -> list[ExperimentSummaryRow]:
    return [
        ExperimentSummaryRow(
            sweep_key=sweep.key,
            sweep_label=sweep.label,
            level=float(level),
            method=method,
            **summaries[method],
        )
        for method in methods
    ]


def rows_as_dicts(result: MainExperimentResult) -> list[dict[str, Any]]:
    """Return the long-form table as plain dictionaries."""

    return [row.as_dict() for row in result.rows]
