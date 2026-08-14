"""NSW real-data local-contrast reconstruction experiment.

The module follows Section 6.2 and Appendix B of the focal paper. It turns
the randomized Dehejia-Wahba NSW sample into local experiment objects and
holds out objects, rather than units, for reconstruction. Target outcomes and
target local standard errors are retained only by the evaluation layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from math import sqrt
from pathlib import Path
from typing import Any, Sequence

import numpy as np

from .methods import _project_to_simplex


NSW_SOURCE_URL = "https://users.nber.org/~rdehejia/data/nsw_dw.dta"
NSW_SOURCE_SHA256 = "d1bd2680a1c6f799f1c6d2455bf29633fdf19be01cb19490621c20a560b4e072"
NSW_COVARIATES = (
    "age",
    "education",
    "black",
    "hispanic",
    "married",
    "nodegree",
    "re74",
    "re75",
)
NSW_SEMANTIC_COVARIATES = NSW_COVARIATES[:6]
NSW_METHODS = (
    "atlas",
    "atlas_no_rejection",
    "semantic_forced",
    "nearest_semantic",
    "global_mean",
)


@dataclass(frozen=True)
class NswExperimentConfig:
    """Fixed protocol for the real-data reconstruction exercise."""

    n_neighbors: int = 50
    n_local_objects: int = 112
    holdout_count: int = 28
    min_treated: int = 8
    min_control: int = 8
    center_norm_quantile: float = 0.95
    radius_quantile: float = 0.95
    max_candidates: int = 24
    repetitions_per_seed: int = 20
    base_seeds: tuple[int, ...] = (20261201, 20261202, 20261203)
    z_value: float = 1.96
    variance_penalty: float = 0.15
    causal_effect_scale: float = 0.80
    semantic_effect_scale: float = 0.35
    nearest_effect_scale: float = 0.55
    global_effect_scale: float = 0.35
    dispersion_weight: float = 0.25
    no_rejection_bias_fraction: float = 0.75
    scientific_tolerance: float = 3.30
    max_weight_iterations: int = 300
    weight_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        if self.n_neighbors < self.min_treated + self.min_control:
            raise ValueError("n_neighbors cannot be smaller than the arm minima.")
        if self.n_local_objects <= self.holdout_count:
            raise ValueError("n_local_objects must exceed holdout_count.")
        if self.holdout_count < 1 or self.max_candidates < 1:
            raise ValueError("holdout_count and max_candidates must be positive.")
        if self.repetitions_per_seed < 1 or not self.base_seeds:
            raise ValueError("The split protocol needs repetitions and base seeds.")
        if not 0.0 < self.center_norm_quantile <= 1.0:
            raise ValueError("center_norm_quantile must lie in (0, 1].")
        if not 0.0 < self.radius_quantile <= 1.0:
            raise ValueError("radius_quantile must lie in (0, 1].")
        if self.z_value <= 0.0 or self.variance_penalty < 0.0:
            raise ValueError("z_value must be positive and variance_penalty nonnegative.")
        scales = (
            self.causal_effect_scale,
            self.semantic_effect_scale,
            self.nearest_effect_scale,
            self.global_effect_scale,
        )
        if any(scale < 0.0 for scale in scales):
            raise ValueError("Effect scales must be nonnegative.")
        if not 0.0 <= self.no_rejection_bias_fraction <= 1.0:
            raise ValueError("no_rejection_bias_fraction must lie in [0, 1].")
        if self.scientific_tolerance < 0.0:
            raise ValueError("scientific_tolerance must be nonnegative.")
        if self.max_weight_iterations < 1 or self.weight_tolerance <= 0.0:
            raise ValueError("Weight optimization controls must be positive.")


@dataclass(frozen=True)
class NswLocalContrast:
    """One observed local randomized contrast in the NSW covariate space."""

    object_id: str
    center_row: int
    neighborhood_rows: tuple[int, ...]
    context: np.ndarray
    semantic_representation: np.ndarray
    causal_representation: np.ndarray
    estimated_effect: float
    standard_error: float
    overlap_score: float
    neighborhood_radius: float
    treated_count: int
    control_count: int

    @property
    def sample_size(self) -> int:
        return self.treated_count + self.control_count


@dataclass(frozen=True)
class NswArchive:
    """The fixed local-object archive and source audit metadata."""

    objects: tuple[NswLocalContrast, ...]
    source_metadata: dict[str, Any]


@dataclass(frozen=True)
class NswPrediction:
    """One method output before the held-out contrast is revealed."""

    method: str
    predicted_effect: float
    interval_lower: float
    interval_upper: float
    accepted: bool
    certificate_radius: float
    statistical_term: float
    representation_term: float
    support_residual: float
    representation_dispersion: float
    candidate_count: int
    effective_source_count: float
    rejection_reason: str | None

    @property
    def rejected(self) -> bool:
        return not self.accepted


@dataclass(frozen=True)
class NswRecord:
    """Evaluation record joining a blind prediction to its held-out reference."""

    method: str
    seed_batch: int
    replicate: int
    split_seed: int
    target_object_id: str
    target_effect_reference: float
    target_standard_error_reference: float
    prediction: NswPrediction


@dataclass(frozen=True)
class NswSummaryRow:
    """Paper-facing pooled metrics for one reconstruction method."""

    method: str
    target_evaluations: int
    seed_batches: int
    mae: float
    median_absolute_error: float
    sign_accuracy: float
    interval_coverage: float
    mean_interval_width: float
    rejection_rate: float
    mean_certificate_radius: float
    between_seed_mae_sd: float | None
    between_seed_rejection_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NswArchiveMapRow:
    """One local object projected onto a deterministic two-dimensional PCA map."""

    object_id: str
    pc1: float
    pc2: float
    atlas_holdout_evaluations: int
    atlas_acceptance_rate: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NswDiagnosticRow:
    """Target-level held-out reconstruction and certificate diagnostic."""

    seed_batch: int
    replicate: int
    split_seed: int
    target_object_id: str
    pc1: float
    pc2: float
    heldout_local_contrast: float
    reconstructed_contrast: float
    absolute_reconstruction_error: float
    accepted: bool
    certificate_radius: float
    support_component: float
    statistical_component: float
    interval_width: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NswExperimentResult:
    """Local archive, blind predictions, and pooled reconstruction metrics."""

    config: NswExperimentConfig
    archive: NswArchive
    records: tuple[NswRecord, ...]
    rows: tuple[NswSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": asdict(self.config),
            "source_metadata": self.archive.source_metadata,
            "local_object_count": len(self.archive.objects),
            "rows": [row.as_dict() for row in self.rows],
        }


@dataclass(frozen=True)
class _RawLocalContrast:
    center_row: int
    neighborhood_rows: tuple[int, ...]
    context: np.ndarray
    estimated_effect: float
    standard_error: float
    overlap_score: float
    neighborhood_radius: float
    treated_count: int
    control_count: int


def build_nsw_local_archive(
    data_path: Path,
    config: NswExperimentConfig | None = None,
) -> NswArchive:
    """Load the committed NSW snapshot and build deterministic local objects."""

    config = config or NswExperimentConfig()
    data_path = Path(data_path)
    raw_bytes = data_path.read_bytes()
    digest = sha256(raw_bytes).hexdigest()
    if digest != NSW_SOURCE_SHA256:
        raise ValueError(
            "NSW source checksum mismatch: "
            f"expected {NSW_SOURCE_SHA256}, found {digest}."
        )

    try:
        import pandas as pd
    except ImportError as error:  # pragma: no cover - environment guard
        raise RuntimeError("pandas is required to read the committed Stata file.") from error

    frame = pd.read_stata(data_path)
    required = {"treat", "re78", *NSW_COVARIATES}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"NSW source is missing columns: {sorted(missing)}")
    if frame[list(required)].isna().any().any():
        raise ValueError("NSW source contains missing values in required fields.")

    treatment = frame["treat"].to_numpy(dtype=int)
    outcomes = frame["re78"].to_numpy(dtype=float) / 1000.0
    covariates = frame[list(NSW_COVARIATES)].to_numpy(dtype=float)
    means = covariates.mean(axis=0)
    scales = covariates.std(axis=0, ddof=1)
    scales = np.where(scales > 1e-12, scales, 1.0)
    standardized = (covariates - means) / scales

    raw_objects = _build_raw_local_contrasts(
        standardized,
        treatment,
        outcomes,
        config,
    )
    selected = _select_spread_objects(raw_objects, standardized, config)
    semantic_matrix = np.vstack(
        [item.context[: len(NSW_SEMANTIC_COVARIATES)] for item in selected]
    )
    causal_matrix = np.column_stack(
        (
            np.vstack([item.context for item in selected]),
            np.asarray([item.overlap_score for item in selected]),
            np.asarray([item.neighborhood_radius for item in selected]),
        )
    )
    semantic_matrix = _standardize_columns(semantic_matrix)
    causal_matrix = _standardize_columns(causal_matrix)
    objects = tuple(
        NswLocalContrast(
            object_id=f"local_{index:03d}",
            center_row=item.center_row,
            neighborhood_rows=item.neighborhood_rows,
            context=item.context.copy(),
            semantic_representation=semantic_matrix[index].copy(),
            causal_representation=causal_matrix[index].copy(),
            estimated_effect=item.estimated_effect,
            standard_error=item.standard_error,
            overlap_score=item.overlap_score,
            neighborhood_radius=item.neighborhood_radius,
            treated_count=item.treated_count,
            control_count=item.control_count,
        )
        for index, item in enumerate(selected)
    )
    source_metadata = {
        "source_url": NSW_SOURCE_URL,
        "source_sha256": digest,
        "source_file": "data/nsw_dw.dta",
        "source_format": "Stata .dta",
        "dataset_rows": int(len(frame)),
        "treated_rows": int(treatment.sum()),
        "control_rows": int((1 - treatment).sum()),
        "outcome": "1978 earnings in thousands of US dollars (re78 / 1000)",
        "covariates": list(NSW_COVARIATES),
        "semantic_coordinates": list(NSW_SEMANTIC_COVARIATES),
        "causal_representation": [
            *NSW_COVARIATES,
            "local_overlap_score",
            "local_neighborhood_radius",
        ],
        "raw_candidate_count": len(raw_objects),
        "selected_local_object_count": len(objects),
    }
    return NswArchive(objects=objects, source_metadata=source_metadata)


def _build_raw_local_contrasts(
    standardized: np.ndarray,
    treatment: np.ndarray,
    outcomes: np.ndarray,
    config: NswExperimentConfig,
) -> tuple[_RawLocalContrast, ...]:
    objects: list[_RawLocalContrast] = []
    for center_row, center in enumerate(standardized):
        distances = np.linalg.norm(standardized - center, axis=1)
        neighbors = np.argsort(distances, kind="stable")[: config.n_neighbors]
        local_treatment = treatment[neighbors]
        treated_count = int(local_treatment.sum())
        control_count = int(len(neighbors) - treated_count)
        if treated_count < config.min_treated or control_count < config.min_control:
            continue
        treated_outcomes = outcomes[neighbors][local_treatment == 1]
        control_outcomes = outcomes[neighbors][local_treatment == 0]
        effect = float(treated_outcomes.mean() - control_outcomes.mean())
        standard_error = float(
            sqrt(
                treated_outcomes.var(ddof=1) / treated_count
                + control_outcomes.var(ddof=1) / control_count
            )
        )
        context = standardized[neighbors].mean(axis=0)
        treatment_share = treated_count / len(neighbors)
        overlap_score = float(4.0 * treatment_share * (1.0 - treatment_share))
        radius = float(
            sqrt(np.mean(np.sum((standardized[neighbors] - context) ** 2, axis=1)))
        )
        objects.append(
            _RawLocalContrast(
                center_row=center_row,
                neighborhood_rows=tuple(int(index) for index in neighbors),
                context=context,
                estimated_effect=effect,
                standard_error=standard_error,
                overlap_score=overlap_score,
                neighborhood_radius=radius,
                treated_count=treated_count,
                control_count=control_count,
            )
        )
    if not objects:
        raise ValueError("No local NSW neighborhoods satisfy the arm minima.")
    return tuple(objects)


def _select_spread_objects(
    objects: tuple[_RawLocalContrast, ...],
    standardized: np.ndarray,
    config: NswExperimentConfig,
) -> tuple[_RawLocalContrast, ...]:
    radii = np.asarray([item.neighborhood_radius for item in objects])
    center_norms = np.asarray(
        [np.linalg.norm(standardized[item.center_row]) for item in objects]
    )
    radius_limit = float(np.quantile(radii, config.radius_quantile))
    center_limit = float(np.quantile(center_norms, config.center_norm_quantile))
    eligible = tuple(
        item
        for item in objects
        if item.neighborhood_radius <= radius_limit + 1e-12
        and np.linalg.norm(standardized[item.center_row]) <= center_limit + 1e-12
    )
    if len(eligible) < config.n_local_objects:
        raise ValueError(
            "Object filters leave fewer candidates than n_local_objects: "
            f"{len(eligible)} < {config.n_local_objects}."
        )
    contexts = np.vstack([item.context for item in eligible])
    centroid = contexts.mean(axis=0)
    selected = [int(np.argmin(np.linalg.norm(contexts - centroid, axis=1)))]
    minimum_distances = np.linalg.norm(contexts - contexts[selected[0]], axis=1)
    while len(selected) < config.n_local_objects:
        minimum_distances[selected] = -1.0
        next_index = int(np.argmax(minimum_distances))
        selected.append(next_index)
        minimum_distances = np.minimum(
            minimum_distances,
            np.linalg.norm(contexts - contexts[next_index], axis=1),
        )
    return tuple(eligible[index] for index in selected)


def _standardize_columns(values: np.ndarray) -> np.ndarray:
    scales = values.std(axis=0, ddof=1)
    scales = np.where(scales > 1e-12, scales, 1.0)
    return (values - values.mean(axis=0)) / scales


def fit_nsw_method(
    method: str,
    archive: Sequence[NswLocalContrast],
    target: NswLocalContrast,
    config: NswExperimentConfig | None = None,
) -> NswPrediction:
    """Fit one method without reading the held-out effect or standard error."""

    config = config or NswExperimentConfig()
    if method not in NSW_METHODS:
        raise ValueError(f"Unknown NSW method: {method}")
    if not archive:
        raise ValueError("The NSW reconstruction archive cannot be empty.")

    semantic = np.vstack([item.semantic_representation for item in archive])
    semantic_distances = np.linalg.norm(
        semantic - target.semantic_representation,
        axis=1,
    )
    semantic_order = np.argsort(semantic_distances, kind="stable")
    if method in {"atlas", "atlas_no_rejection"}:
        indices = semantic_order[: min(config.max_candidates, len(archive))]
        representations = np.vstack(
            [archive[index].causal_representation for index in indices]
        )
        standard_errors = np.asarray(
            [archive[index].standard_error for index in indices]
        )
        weights = _optimize_weights(
            representations,
            target.causal_representation,
            standard_errors,
            config,
        )
        scale = config.causal_effect_scale
        representation_name = "causal"
    elif method == "semantic_forced":
        indices = semantic_order[: min(config.max_candidates, len(archive))]
        distances = semantic_distances[indices]
        similarities = 1.0 / np.maximum(distances, 0.05)
        weights = similarities / similarities.sum()
        representations = semantic[indices]
        scale = config.semantic_effect_scale
        representation_name = "semantic"
    elif method == "nearest_semantic":
        indices = semantic_order[:1]
        weights = np.ones(1, dtype=float)
        representations = semantic[indices]
        scale = config.nearest_effect_scale
        representation_name = "semantic"
    else:
        indices = np.arange(len(archive), dtype=int)
        weights = np.full(len(indices), 1.0 / len(indices))
        representations = semantic
        scale = config.global_effect_scale
        representation_name = "semantic"

    source_effects = np.asarray([archive[index].estimated_effect for index in indices])
    source_standard_errors = np.asarray(
        [archive[index].standard_error for index in indices]
    )
    predicted_effect = float(weights @ source_effects)
    target_representation = (
        target.causal_representation
        if representation_name == "causal"
        else target.semantic_representation
    )
    weighted_representation = weights @ representations
    support_residual = float(
        np.linalg.norm(target_representation - weighted_representation)
    )
    dispersion = float(
        sqrt(
            np.sum(
                weights
                * np.sum((representations - weighted_representation) ** 2, axis=1)
            )
        )
    )
    statistical_term = float(
        config.z_value * sqrt(np.sum(weights**2 * source_standard_errors**2))
    )
    if method == "global_mean":
        representation_term = scale * support_residual
    else:
        representation_term = scale * (
            support_residual + config.dispersion_weight * dispersion
        )
    if method == "atlas_no_rejection":
        representation_term *= config.no_rejection_bias_fraction
    certificate_radius = statistical_term + representation_term
    accepted = method != "atlas" or (
        certificate_radius <= config.scientific_tolerance + 1e-12
    )
    effective_source_count = float(1.0 / np.sum(weights**2))
    return NswPrediction(
        method=method,
        predicted_effect=predicted_effect,
        interval_lower=predicted_effect - certificate_radius,
        interval_upper=predicted_effect + certificate_radius,
        accepted=accepted,
        certificate_radius=certificate_radius,
        statistical_term=statistical_term,
        representation_term=representation_term,
        support_residual=support_residual,
        representation_dispersion=dispersion,
        candidate_count=len(indices),
        effective_source_count=effective_source_count,
        rejection_reason=(
            None if accepted else "certificate exceeds scientific tolerance"
        ),
    )


def _optimize_weights(
    representations: np.ndarray,
    target: np.ndarray,
    standard_errors: np.ndarray,
    config: NswExperimentConfig,
) -> np.ndarray:
    error_scale = max(float(np.median(standard_errors)), 1e-12)
    normalized_variances = (standard_errors / error_scale) ** 2

    def objective(weights: np.ndarray) -> float:
        residual = weights @ representations - target
        return float(
            residual @ residual
            + config.variance_penalty
            * np.sum(weights**2 * normalized_variances)
        )

    def gradient(weights: np.ndarray) -> np.ndarray:
        residual = weights @ representations - target
        return (
            2.0 * representations @ residual
            + 2.0
            * config.variance_penalty
            * weights
            * normalized_variances
        )

    weights = np.full(len(representations), 1.0 / len(representations))
    step = 0.10
    current = objective(weights)
    for _ in range(config.max_weight_iterations):
        proposal = _project_to_simplex(weights - step * gradient(weights))
        proposed = objective(proposal)
        if proposed <= current + 1e-14:
            change = float(np.linalg.norm(proposal - weights))
            weights, current = proposal, proposed
            step = min(step * 1.05, 1.0)
            if change <= config.weight_tolerance:
                break
        else:
            step *= 0.5
            if step < 1e-12:
                break
    return weights


def run_nsw_experiment(
    data_path: Path,
    config: NswExperimentConfig | None = None,
) -> NswExperimentResult:
    """Run shared held-out splits across all five reconstruction methods."""

    config = config or NswExperimentConfig()
    archive = build_nsw_local_archive(data_path, config)
    records: list[NswRecord] = []
    for seed_batch, base_seed in enumerate(config.base_seeds):
        sequences = np.random.SeedSequence(base_seed).spawn(
            config.repetitions_per_seed
        )
        for replicate, sequence in enumerate(sequences):
            split_seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
            rng = np.random.default_rng(sequence)
            target_indices = np.sort(
                rng.choice(
                    len(archive.objects),
                    size=config.holdout_count,
                    replace=False,
                )
            )
            target_set = set(int(index) for index in target_indices)
            sources = tuple(
                item
                for index, item in enumerate(archive.objects)
                if index not in target_set
            )
            for target_index in target_indices:
                target = archive.objects[int(target_index)]
                for method in NSW_METHODS:
                    prediction = fit_nsw_method(method, sources, target, config)
                    records.append(
                        NswRecord(
                            method=method,
                            seed_batch=seed_batch,
                            replicate=replicate,
                            split_seed=split_seed,
                            target_object_id=target.object_id,
                            target_effect_reference=target.estimated_effect,
                            target_standard_error_reference=target.standard_error,
                            prediction=prediction,
                        )
                    )
    rows = tuple(
        _summarize_method(
            method,
            [record for record in records if record.method == method],
        )
        for method in NSW_METHODS
    )
    return NswExperimentResult(
        config=config,
        archive=archive,
        records=tuple(records),
        rows=rows,
    )


def nsw_archive_map_rows(
    result: NswExperimentResult,
) -> tuple[NswArchiveMapRow, ...]:
    """Project public causal representations and attach holdout release rates."""

    matrix = np.vstack(
        [item.causal_representation for item in result.archive.objects]
    )
    centered = matrix - matrix.mean(axis=0)
    _, _, right = np.linalg.svd(centered, full_matrices=False)
    components = right[:2].copy()
    for index in range(components.shape[0]):
        pivot = int(np.argmax(np.abs(components[index])))
        if components[index, pivot] < 0.0:
            components[index] *= -1.0
    scores = centered @ components.T
    atlas_records = [record for record in result.records if record.method == "atlas"]
    rows = []
    for index, item in enumerate(result.archive.objects):
        heldout = [
            record
            for record in atlas_records
            if record.target_object_id == item.object_id
        ]
        rows.append(
            NswArchiveMapRow(
                object_id=item.object_id,
                pc1=float(scores[index, 0]),
                pc2=float(scores[index, 1]),
                atlas_holdout_evaluations=len(heldout),
                atlas_acceptance_rate=(
                    float(np.mean([record.prediction.accepted for record in heldout]))
                    if heldout
                    else None
                ),
            )
        )
    return tuple(rows)


def nsw_diagnostic_rows(
    result: NswExperimentResult,
) -> tuple[NswDiagnosticRow, ...]:
    """Return ATLAS target records for paper diagnostics without refitting."""

    map_rows = {row.object_id: row for row in nsw_archive_map_rows(result)}
    rows = []
    for record in result.records:
        if record.method != "atlas":
            continue
        prediction = record.prediction
        location = map_rows[record.target_object_id]
        rows.append(
            NswDiagnosticRow(
                seed_batch=record.seed_batch,
                replicate=record.replicate,
                split_seed=record.split_seed,
                target_object_id=record.target_object_id,
                pc1=location.pc1,
                pc2=location.pc2,
                heldout_local_contrast=record.target_effect_reference,
                reconstructed_contrast=prediction.predicted_effect,
                absolute_reconstruction_error=abs(
                    prediction.predicted_effect - record.target_effect_reference
                ),
                accepted=prediction.accepted,
                certificate_radius=prediction.certificate_radius,
                support_component=prediction.representation_term,
                statistical_component=prediction.statistical_term,
                interval_width=prediction.interval_upper - prediction.interval_lower,
            )
        )
    return tuple(rows)


def _summarize_method(
    method: str,
    records: Sequence[NswRecord],
) -> NswSummaryRow:
    if not records:
        raise ValueError(f"No NSW records supplied for method {method}.")
    errors = np.asarray(
        [
            record.prediction.predicted_effect
            - record.target_effect_reference
            for record in records
        ]
    )
    coverage = np.asarray(
        [
            record.prediction.interval_lower
            <= record.target_effect_reference
            <= record.prediction.interval_upper
            for record in records
        ]
    )
    seed_batches = sorted({record.seed_batch for record in records})
    seed_mae = []
    seed_rejection = []
    for seed_batch in seed_batches:
        selected = [record for record in records if record.seed_batch == seed_batch]
        seed_mae.append(
            float(
                np.mean(
                    [
                        abs(
                            record.prediction.predicted_effect
                            - record.target_effect_reference
                        )
                        for record in selected
                    ]
                )
            )
        )
        seed_rejection.append(
            float(np.mean([record.prediction.rejected for record in selected]))
        )
    return NswSummaryRow(
        method=method,
        target_evaluations=len(records),
        seed_batches=len(seed_batches),
        mae=float(np.mean(np.abs(errors))),
        median_absolute_error=float(np.median(np.abs(errors))),
        sign_accuracy=float(
            np.mean(
                [
                    np.sign(record.prediction.predicted_effect)
                    == np.sign(record.target_effect_reference)
                    for record in records
                ]
            )
        ),
        interval_coverage=float(np.mean(coverage)),
        mean_interval_width=float(
            np.mean(
                [
                    record.prediction.interval_upper
                    - record.prediction.interval_lower
                    for record in records
                ]
            )
        ),
        rejection_rate=float(
            np.mean([record.prediction.rejected for record in records])
        ),
        mean_certificate_radius=float(
            np.mean([record.prediction.certificate_radius for record in records])
        ),
        between_seed_mae_sd=(
            float(np.std(seed_mae, ddof=1)) if len(seed_mae) > 1 else None
        ),
        between_seed_rejection_sd=(
            float(np.std(seed_rejection, ddof=1))
            if len(seed_rejection) > 1
            else None
        ),
    )
