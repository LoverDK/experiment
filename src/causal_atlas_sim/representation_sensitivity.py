"""Two-dimensional representation-sensitivity experiment.

The experiment varies a hidden-only target shift and the declared uncertainty
of its public proxy. ATLAS uses the complete public representation, whereas the
semantic baseline is restricted to the two semantic coordinates ``(s1, s2)``.
All comparisons are paired on the same generated targets.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

import numpy as np

from .dgp import SimulationConfig, generate_minimal_archive
from .methods import (
    AtlasConfig,
    fit_causal_atlas,
    fit_semantic_forced_composition,
)


@dataclass(frozen=True)
class RepresentationSensitivityConfig:
    """Fixed shared-seed protocol for the hidden-shift by proxy grid."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20260901, 20260902, 20260903)
    hidden_shift_fractions: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8)
    proxy_uncertainties: tuple[float, ...] = (0.05, 0.10, 0.20, 0.30, 0.40)
    semantic_dimensions: tuple[int, ...] = (0, 1)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    atlas_config: AtlasConfig = field(default_factory=AtlasConfig)

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2 or not self.base_seeds:
            raise ValueError("The sensitivity protocol needs repetitions and base seeds.")
        if tuple(sorted(set(self.hidden_shift_fractions))) != self.hidden_shift_fractions:
            raise ValueError("hidden_shift_fractions must be strictly increasing.")
        if any(not 0.0 <= value <= 1.0 for value in self.hidden_shift_fractions):
            raise ValueError("hidden shift fractions must lie in [0, 1].")
        if tuple(sorted(set(self.proxy_uncertainties))) != self.proxy_uncertainties:
            raise ValueError("proxy_uncertainties must be strictly increasing.")
        if any(value <= 0.0 for value in self.proxy_uncertainties):
            raise ValueError("proxy uncertainties must be positive.")
        if not self.semantic_dimensions:
            raise ValueError("semantic_dimensions cannot be empty.")


@dataclass(frozen=True)
class RepresentationSensitivityRecord:
    hidden_shift_fraction: float
    proxy_uncertainty: float
    seed_batch: int
    replicate: int
    seed: int
    realized_hidden_shift: float
    atlas_accepted: bool
    certificate_radius: float
    atlas_absolute_error: float
    semantic_absolute_error: float


@dataclass(frozen=True)
class RepresentationSensitivityRow:
    hidden_shift_fraction: float
    proxy_uncertainty: float
    repetitions: int
    seed_batches: int
    mean_realized_hidden_shift: float
    atlas_acceptance_rate: float
    atlas_accepted_mae: float | None
    atlas_no_rejection_mae: float
    semantic_forced_mae: float
    representation_advantage: float
    selection_gain: float | None
    mean_certificate_radius: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepresentationSensitivityResult:
    config: RepresentationSensitivityConfig
    records: tuple[RepresentationSensitivityRecord, ...]
    rows: tuple[RepresentationSensitivityRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "hidden_shift_fractions": list(self.config.hidden_shift_fractions),
                "proxy_uncertainties": list(self.config.proxy_uncertainties),
                "semantic_dimensions": list(self.config.semantic_dimensions),
                "dgp_config": asdict(self.config.dgp_config),
                "atlas_config": asdict(self.config.atlas_config),
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_representation_sensitivity(
    config: RepresentationSensitivityConfig | None = None,
) -> RepresentationSensitivityResult:
    """Run paired representation and selection comparisons on the full grid."""

    config = config or RepresentationSensitivityConfig()
    records: list[RepresentationSensitivityRecord] = []
    atlas_config = replace(config.atlas_config, representation_dimensions=None)
    semantic_config = replace(
        config.atlas_config,
        representation_dimensions=config.semantic_dimensions,
    )
    for hidden_shift in config.hidden_shift_fractions:
        for proxy_uncertainty in config.proxy_uncertainties:
            dgp_config = replace(
                config.dgp_config,
                target_shift_fraction=0.0,
                target_hidden_shift_fraction=hidden_shift,
                moderator_sensitivity_radius=proxy_uncertainty,
                moderator_proxy_half_width=proxy_uncertainty / 2.0,
            )
            for seed_batch, base_seed in enumerate(config.base_seeds):
                sequences = np.random.SeedSequence(base_seed).spawn(
                    config.repetitions_per_seed
                )
                for replicate, sequence in enumerate(sequences):
                    seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
                    generated = generate_minimal_archive(dgp_config, seed=seed)
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
                    if atlas.raw_point_estimate is None or semantic.raw_point_estimate is None:
                        raise RuntimeError("The fixed sensitivity DGP produced no usable estimate.")
                    supported_hidden = float(
                        generated.target_support_weights
                        @ np.asarray([item.mechanism.h for item in generated.archive])
                    )
                    truth = generated.target.true_effect
                    records.append(
                        RepresentationSensitivityRecord(
                            hidden_shift_fraction=hidden_shift,
                            proxy_uncertainty=proxy_uncertainty,
                            seed_batch=seed_batch,
                            replicate=replicate,
                            seed=seed,
                            realized_hidden_shift=abs(
                                generated.target.mechanism.h - supported_hidden
                            ),
                            atlas_accepted=atlas.accepted,
                            certificate_radius=atlas.certificate.radius,
                            atlas_absolute_error=abs(atlas.raw_point_estimate - truth),
                            semantic_absolute_error=abs(
                                semantic.raw_point_estimate - truth
                            ),
                        )
                    )
    rows = tuple(
        _summarize_cell(config, records, hidden_shift, proxy_uncertainty)
        for hidden_shift in config.hidden_shift_fractions
        for proxy_uncertainty in config.proxy_uncertainties
    )
    return RepresentationSensitivityResult(
        config=config,
        records=tuple(records),
        rows=rows,
    )


def _summarize_cell(
    config: RepresentationSensitivityConfig,
    records: list[RepresentationSensitivityRecord],
    hidden_shift: float,
    proxy_uncertainty: float,
) -> RepresentationSensitivityRow:
    selected = [
        record
        for record in records
        if record.hidden_shift_fraction == hidden_shift
        and record.proxy_uncertainty == proxy_uncertainty
    ]
    atlas_errors = np.asarray([record.atlas_absolute_error for record in selected])
    semantic_errors = np.asarray(
        [record.semantic_absolute_error for record in selected]
    )
    accepted_errors = np.asarray(
        [record.atlas_absolute_error for record in selected if record.atlas_accepted]
    )
    atlas_mae = float(np.mean(atlas_errors))
    semantic_mae = float(np.mean(semantic_errors))
    accepted_mae = float(np.mean(accepted_errors)) if accepted_errors.size else None
    return RepresentationSensitivityRow(
        hidden_shift_fraction=hidden_shift,
        proxy_uncertainty=proxy_uncertainty,
        repetitions=len(selected),
        seed_batches=len(config.base_seeds),
        mean_realized_hidden_shift=float(
            np.mean([record.realized_hidden_shift for record in selected])
        ),
        atlas_acceptance_rate=float(
            np.mean([record.atlas_accepted for record in selected])
        ),
        atlas_accepted_mae=accepted_mae,
        atlas_no_rejection_mae=atlas_mae,
        semantic_forced_mae=semantic_mae,
        representation_advantage=semantic_mae - atlas_mae,
        selection_gain=(atlas_mae - accepted_mae if accepted_mae is not None else None),
        mean_certificate_radius=float(
            np.mean([record.certificate_radius for record in selected])
        ),
    )
