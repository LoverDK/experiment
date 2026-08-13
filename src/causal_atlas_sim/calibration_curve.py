"""Coverage--width calibration curves at several nominal confidence levels."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from statistics import NormalDist
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .methods import AtlasConfig, fit_causal_atlas, fit_semantic_forced_composition


@dataclass(frozen=True)
class CalibrationCurveConfig:
    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260841, 20260842, 20260843)
    confidence_levels: tuple[float, ...] = (0.80, 0.90, 0.95, 0.975)
    scientific_tolerance: float = 1.65
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2 or not self.base_seeds:
            raise ValueError("repetitions and base_seeds must be nonempty.")
        if tuple(sorted(set(self.confidence_levels))) != self.confidence_levels:
            raise ValueError("confidence_levels must be strictly increasing.")
        if any(not 0.0 < level < 1.0 for level in self.confidence_levels):
            raise ValueError("confidence levels must lie in (0, 1).")


@dataclass(frozen=True)
class CalibrationCurveRow:
    confidence_level: float
    policy: str
    release_rate: float
    empirical_coverage: float
    mean_width: float
    conditional_coverage: float | None
    conditional_width: float | None
    conditional_mae: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CalibrationCurveResult:
    config: CalibrationCurveConfig
    rows: tuple[CalibrationCurveRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "confidence_levels": list(self.config.confidence_levels),
                "scientific_tolerance": self.config.scientific_tolerance,
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_calibration_curve_experiment(
    config: CalibrationCurveConfig | None = None,
) -> CalibrationCurveResult:
    """Evaluate honest and intentionally misspecified intervals on shared draws."""

    config = config or CalibrationCurveConfig()
    records: dict[str, list[dict[str, Any]]] = {
        "honest_atlas": [],
        "wald_only": [],
        "semantic_forced": [],
        "understated_smoothness": [],
        "no_hidden_moderator_inflation": [],
    }
    for base_seed in config.base_seeds:
        for sequence in np.random.SeedSequence(base_seed).spawn(config.repetitions_per_seed):
            seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
            generated = generate_minimal_archive(config.dgp_config, seed=seed)
            for level in config.confidence_levels:
                zeta = 1.0 - level
                honest_config = replace(
                    config.atlas_config,
                    zeta=zeta,
                    scientific_tolerance=config.scientific_tolerance,
                )
                honest = fit_causal_atlas(generated.archive, generated.target, honest_config)
                understated = fit_causal_atlas(
                    generated.archive,
                    generated.target,
                    replace(
                        honest_config,
                        effect_lipschitz_bound=0.20,
                        effect_curvature_bound=0.05,
                    ),
                )
                no_hidden = fit_causal_atlas(
                    generated.archive,
                    generated.target,
                    replace(honest_config, hidden_moderator_lipschitz_bound=0.0),
                )
                semantic = fit_semantic_forced_composition(
                    generated.archive, generated.target, honest_config
                )
                raw = honest.raw_point_estimate
                if raw is None:
                    continue
                truth = generated.target.true_effect
                for policy, result, estimate in (
                    ("honest_atlas", honest, raw),
                    ("understated_smoothness", understated, raw),
                    ("no_hidden_moderator_inflation", no_hidden, raw),
                    ("semantic_forced", semantic, semantic.raw_point_estimate),
                ):
                    records[policy].append(
                        {
                            "level": level,
                            "truth": truth,
                            "estimate": estimate,
                            "lower": result.interval_lower,
                            "upper": result.interval_upper,
                            "accepted": result.accepted,
                        }
                    )
                se = np.sqrt(sum(
                    weight**2 * source.standard_error_certificate**2
                    for weight, source in zip(honest.weights, generated.archive, strict=True)
                ))
                z = NormalDist().inv_cdf(1.0 - zeta / 2.0)
                records["wald_only"].append(
                    {
                        "level": level,
                        "truth": truth,
                        "estimate": raw,
                        "lower": raw - z * se,
                        "upper": raw + z * se,
                        "accepted": True,
                    }
                )
    rows: list[CalibrationCurveRow] = []
    for level in config.confidence_levels:
        for policy, values in records.items():
            selected = [value for value in values if value["level"] == level]
            widths = np.asarray(
                [item["upper"] - item["lower"] for item in selected],
                dtype=float,
            )
            coverage = np.asarray(
                [
                    item["lower"] <= item["truth"] <= item["upper"]
                    for item in selected
                ],
                dtype=bool,
            )
            accepted_mask = np.asarray(
                [item["accepted"] for item in selected],
                dtype=bool,
            )
            errors = np.asarray(
                [abs(item["estimate"] - item["truth"]) for item in selected],
                dtype=float,
            )
            accepted_errors = errors[accepted_mask]
            accepted_coverage = coverage[accepted_mask]
            accepted_widths = widths[accepted_mask]
            rows.append(CalibrationCurveRow(
                confidence_level=float(level), policy=policy,
                release_rate=float(np.mean(accepted_mask)),
                empirical_coverage=float(np.mean(coverage)),
                mean_width=float(np.mean(widths)),
                conditional_coverage=(float(np.mean(accepted_coverage)) if accepted_coverage.size else None),
                conditional_width=(float(np.mean(accepted_widths)) if accepted_widths.size else None),
                conditional_mae=(float(np.mean(accepted_errors)) if accepted_errors.size else None),
            ))
    return CalibrationCurveResult(config=config, rows=tuple(rows))
