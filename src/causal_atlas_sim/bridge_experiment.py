"""Synthetic bridge-design experiment for Definition 5.2 and Theorem 5.6.

The bridge planner works with the same public mechanism representation,
uncertainty certificates, and moderator radii available to Causal ATLAS.  It
does not inspect target effects or true mechanism coordinates.  Those values
are retained only to evaluate whether a selected bridge closed the true
mechanism-support gap.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from itertools import combinations
from typing import Any, Sequence

import numpy as np

from .dgp import (
    ExperimentData,
    Mechanism,
    SimulationConfig,
    effect_surface,
    generate_minimal_archive,
)
from .algorithm1 import (
    Algorithm1Config,
    BridgeCandidate,
    _candidate_experiment,
    run_algorithm1,
)
from .methods import AtlasConfig, _project_to_simplex
from .partial_identification import construct_partial_identification_interval


@dataclass(frozen=True)
class BridgeScenario:
    """One degree of target support mismatch before bridge acquisition."""

    key: str
    label: str
    target_shift_fraction: float

    def __post_init__(self) -> None:
        if not self.key or not self.label:
            raise ValueError("A bridge scenario needs a key and label.")
        if not 0.0 <= self.target_shift_fraction <= 1.0:
            raise ValueError("target_shift_fraction must lie in [0, 1].")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_bridge_scenarios() -> tuple[BridgeScenario, ...]:
    """Return support through severe-mismatch scenarios for bridge planning."""

    return (
        BridgeScenario("supported", "supported target", 0.0),
        BridgeScenario("moderate", "moderate mismatch", 0.25),
        BridgeScenario("strong", "strong mismatch", 0.60),
        BridgeScenario("severe", "severe mismatch", 0.80),
    )


@dataclass(frozen=True)
class BridgePolicy:
    """Selection policy and the representation coordinates it is allowed to use."""

    key: str
    label: str
    planning_dimensions: tuple[int, ...] | None

    def __post_init__(self) -> None:
        if not self.key or not self.label:
            raise ValueError("A bridge policy needs a key and label.")
        if self.planning_dimensions is not None and not self.planning_dimensions:
            raise ValueError("planning_dimensions cannot be empty.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "planning_dimensions": (
                list(self.planning_dimensions)
                if self.planning_dimensions is not None
                else None
            ),
        }


def default_bridge_policies() -> tuple[BridgePolicy, ...]:
    """Return causal-support, semantic-only, and random bridge policies."""

    return (
        BridgePolicy(
            "causal_greedy",
            "causal-support greedy",
            (0, 1, 2, 3),
        ),
        BridgePolicy(
            "semantic_greedy",
            "semantic-only greedy",
            (0, 1),
        ),
        BridgePolicy("random", "random bridge", None),
    )


@dataclass(frozen=True)
class BridgeExperimentConfig:
    """Fixed protocol for synthetic bridge-design evaluation."""

    repetitions_per_seed: int = 100
    base_seeds: tuple[int, ...] = (20261111, 20261112, 20261113)
    dgp_config: SimulationConfig = field(default_factory=SimulationConfig)
    scenarios: tuple[BridgeScenario, ...] = field(
        default_factory=default_bridge_scenarios
    )
    policies: tuple[BridgePolicy, ...] = field(
        default_factory=default_bridge_policies
    )
    bridge_budget: int = 4
    bridge_standard_error: float = 0.10
    selection_error_bound: float = 0.01
    support_tolerance: float = 0.0
    max_singletons: int = 4
    bridge_quadrature_points: int = 3
    zeta: float = 0.05
    variance_penalty: float = 0.25
    max_weight_iterations: int = 80
    weight_tolerance: float = 1e-11

    def __post_init__(self) -> None:
        if self.repetitions_per_seed < 2:
            raise ValueError("At least two repetitions per seed are required.")
        if not self.base_seeds or not self.scenarios or not self.policies:
            raise ValueError("Seeds, scenarios, and policies must be nonempty.")
        if self.bridge_budget < 1:
            raise ValueError("bridge_budget must be positive.")
        if self.bridge_standard_error <= 0.0:
            raise ValueError("bridge_standard_error must be positive.")
        if self.selection_error_bound < 0.0:
            raise ValueError("selection_error_bound must be nonnegative.")
        if self.support_tolerance < 0.0:
            raise ValueError("support_tolerance must be nonnegative.")
        if self.max_singletons < 1 or self.bridge_quadrature_points < 1:
            raise ValueError("partial-ID and quadrature controls must be positive.")
        if not 0.0 < self.zeta < 1.0:
            raise ValueError("zeta must lie in (0, 1).")
        if self.variance_penalty < 0.0:
            raise ValueError("variance_penalty must be nonnegative.")
        if self.max_weight_iterations < 1 or self.weight_tolerance <= 0.0:
            raise ValueError("weight-optimizer controls must be positive.")


@dataclass(frozen=True)
class BridgeRecord:
    """One policy path after a shared archive and bridge library are generated."""

    scenario_key: str
    scenario_label: str
    policy_key: str
    policy_label: str
    seed_batch: int
    replicate: int
    seed: int
    selected_candidate_keys: tuple[str, ...]
    selected_candidate_families: tuple[str, ...]
    evaluation_diameter_path: tuple[float, ...]
    planning_diameter_path: tuple[float, ...]
    stopping_reason: str | None
    initial_oracle_hull_distance: float
    final_oracle_hull_distance: float
    mean_selected_measurement_absolute_error: float
    mean_selection_error: float | None

    @property
    def initial_diameter(self) -> float:
        return self.evaluation_diameter_path[0]

    @property
    def final_diameter(self) -> float | None:
        value = self.evaluation_diameter_path[-1]
        return value if np.isfinite(value) else None

    @property
    def diameter_shrinkage(self) -> float | None:
        if self.final_diameter is None:
            return None
        return self.initial_diameter - self.final_diameter

    @property
    def planning_consistent(self) -> bool:
        return bool(np.all(np.isfinite(self.planning_diameter_path)))

    @property
    def evaluation_consistent(self) -> bool:
        return bool(np.all(np.isfinite(self.evaluation_diameter_path)))


@dataclass(frozen=True)
class BridgeSummaryRow:
    """Policy-level value-of-information summary for one support scenario."""

    scenario_key: str
    scenario_label: str
    policy_key: str
    policy_label: str
    repetitions: int
    seed_batches: int
    bridge_budget: int
    completed_repetitions: int
    budget_completion_rate: float
    mean_selected_bridge_count: float
    planning_inconsistency_rate: float
    evaluation_inconsistency_rate: float
    finite_final_diameter_repetitions: int
    mean_initial_diameter: float
    mean_final_diameter: float | None
    mean_diameter_shrinkage: float | None
    shrinkage_fraction: float | None
    mean_initial_oracle_hull_distance: float
    mean_final_oracle_hull_distance: float
    mean_selected_measurement_absolute_error: float
    mean_selection_error: float | None
    between_seed_final_diameter_sd: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BridgeBudgetPathRow:
    """Mean evaluation diameter at one realized bridge budget."""

    scenario_key: str
    scenario_label: str
    policy_key: str
    policy_label: str
    budget: int
    repetitions: int
    finite_repetitions: int
    mean_diameter: float | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BridgeExperimentResult:
    """Records and summaries for the fixed Stage 11 protocol."""

    config: BridgeExperimentConfig
    records: tuple[BridgeRecord, ...]
    rows: tuple[BridgeSummaryRow, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "repetitions_per_seed": self.config.repetitions_per_seed,
                "base_seeds": list(self.config.base_seeds),
                "dgp_config": asdict(self.config.dgp_config),
                "scenarios": [scenario.as_dict() for scenario in self.config.scenarios],
                "policies": [policy.as_dict() for policy in self.config.policies],
                "bridge_budget": self.config.bridge_budget,
                "bridge_standard_error": self.config.bridge_standard_error,
                "selection_error_bound": self.config.selection_error_bound,
                "support_tolerance": self.config.support_tolerance,
                "max_singletons": self.config.max_singletons,
                "bridge_quadrature_points": self.config.bridge_quadrature_points,
                "zeta": self.config.zeta,
                "variance_penalty": self.config.variance_penalty,
                "max_weight_iterations": self.config.max_weight_iterations,
                "weight_tolerance": self.config.weight_tolerance,
            },
            "rows": [row.as_dict() for row in self.rows],
        }


def run_bridge_experiment(
    config: BridgeExperimentConfig | None = None,
) -> BridgeExperimentResult:
    """Run shared-data bridge-policy comparisons for Theorem 5.6."""

    config = config or BridgeExperimentConfig()
    records: list[BridgeRecord] = []
    for scenario in config.scenarios:
        dgp_config = _scenario_dgp_config(config.dgp_config, scenario)
        for seed_batch, base_seed in enumerate(config.base_seeds):
            sequences = np.random.SeedSequence(base_seed).spawn(
                config.repetitions_per_seed
            )
            for replicate, sequence in enumerate(sequences):
                seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
                generated = generate_minimal_archive(dgp_config, seed=seed)
                streams = np.random.SeedSequence(seed).spawn(
                    len(config.policies) + 1
                )
                candidates = _build_bridge_library(
                    generated.target,
                    config,
                    np.random.default_rng(streams[0]),
                )
                if config.bridge_budget > len(candidates):
                    raise ValueError("bridge_budget exceeds candidate library size.")
                for policy_index, policy in enumerate(config.policies, start=1):
                    records.append(
                        _run_policy(
                            scenario,
                            policy,
                            generated.archive,
                            generated.target,
                            candidates,
                            config,
                            seed_batch,
                            replicate,
                            seed,
                            np.random.default_rng(streams[policy_index]),
                        )
                    )
    return BridgeExperimentResult(
        config=config,
        records=tuple(records),
        rows=_summarize_records(records, config),
    )


def bridge_budget_path_rows(
    result: BridgeExperimentResult,
) -> tuple[BridgeBudgetPathRow, ...]:
    """Summarize stored diameter paths without rerunning bridge selection."""

    rows: list[BridgeBudgetPathRow] = []
    for scenario in result.config.scenarios:
        for policy in result.config.policies:
            selected = [
                record
                for record in result.records
                if record.scenario_key == scenario.key
                and record.policy_key == policy.key
            ]
            for budget in range(result.config.bridge_budget + 1):
                values = [
                    record.evaluation_diameter_path[
                        min(budget, len(record.evaluation_diameter_path) - 1)
                    ]
                    for record in selected
                ]
                finite = [value for value in values if np.isfinite(value)]
                rows.append(
                    BridgeBudgetPathRow(
                        scenario_key=scenario.key,
                        scenario_label=scenario.label,
                        policy_key=policy.key,
                        policy_label=policy.label,
                        budget=budget,
                        repetitions=len(values),
                        finite_repetitions=len(finite),
                        mean_diameter=(float(np.mean(finite)) if finite else None),
                    )
                )
    return tuple(rows)


def _scenario_dgp_config(
    base: SimulationConfig,
    scenario: BridgeScenario,
) -> SimulationConfig:
    return SimulationConfig(
        n_archive=base.n_archive,
        n_units_per_experiment=base.n_units_per_experiment,
        n_units_target=base.n_units_target,
        propensity=base.propensity,
        overlap_lower_bound=base.overlap_lower_bound,
        outcome_noise_sd=base.outcome_noise_sd,
        moderator_sensitivity_radius=base.moderator_sensitivity_radius,
        moderator_proxy_half_width=base.moderator_proxy_half_width,
        archive_moderator_radius_spread=base.archive_moderator_radius_spread,
        target_shift_fraction=scenario.target_shift_fraction,
        target_shift_anchor=base.target_shift_anchor,
    )


def _build_bridge_library(
    target: ExperimentData,
    config: BridgeExperimentConfig,
    rng: np.random.Generator,
) -> tuple[BridgeCandidate, ...]:
    """Create a public bridge library containing causal and semantic decoys."""

    offsets = (
        ("causal_full_1", "causal_full", (0.15, 0.10, 0.10, 0.08)),
        ("causal_full_2", "causal_full", (-0.12, 0.08, -0.10, -0.05)),
        ("causal_full_3", "causal_full", (0.08, -0.15, 0.06, 0.12)),
        ("causal_full_4", "causal_full", (-0.10, -0.10, 0.14, -0.12)),
        ("semantic_trap_1", "semantic_trap", (0.05, 0.04, 0.65, 0.65)),
        ("semantic_trap_2", "semantic_trap", (-0.04, -0.05, -0.65, 0.55)),
        ("semantic_trap_3", "semantic_trap", (0.06, -0.03, 0.55, -0.65)),
        ("semantic_trap_4", "semantic_trap", (-0.05, 0.04, -0.55, -0.55)),
        ("mixed_1", "mixed", (0.32, -0.22, 0.18, -0.28)),
        ("mixed_2", "mixed", (-0.28, 0.24, -0.22, 0.26)),
        ("mixed_3", "mixed", (0.24, 0.30, -0.30, 0.18)),
        ("mixed_4", "mixed", (-0.30, -0.24, 0.26, -0.20)),
    )
    candidates: list[BridgeCandidate] = []
    for key, family, offset in offsets:
        observed = np.clip(
            target.observed_representation + np.asarray(offset, dtype=float),
            -1.0,
            1.0,
        )
        mechanism_values = observed.copy()
        mechanism_values[2] = float(
            np.clip(
                observed[2]
                + rng.uniform(
                    -target.moderator_sensitivity_radius / 2.0,
                    target.moderator_sensitivity_radius / 2.0,
                ),
                -1.0,
                1.0,
            )
        )
        mechanism = Mechanism.from_array(mechanism_values)
        true_effect = effect_surface(mechanism)
        candidates.append(
            BridgeCandidate(
                key=key,
                family=family,
                mechanism=mechanism,
                observed_representation=observed,
                standard_error=config.bridge_standard_error,
                moderator_sensitivity_radius=target.moderator_sensitivity_radius,
                true_effect=true_effect,
                observed_effect=float(
                    true_effect + config.bridge_standard_error * rng.normal()
                ),
            )
        )
    return tuple(candidates)


def _run_policy(
    scenario: BridgeScenario,
    policy: BridgePolicy,
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    candidates: tuple[BridgeCandidate, ...],
    config: BridgeExperimentConfig,
    seed_batch: int,
    replicate: int,
    seed: int,
    rng: np.random.Generator,
) -> BridgeRecord:
    dimensions = policy.planning_dimensions or (0, 1, 2, 3)
    algorithm_result = run_algorithm1(
        archive,
        target,
        candidates,
        Algorithm1Config(
            atlas_config=AtlasConfig(
                scientific_tolerance=config.support_tolerance,
                zeta=config.zeta,
            ),
            max_singletons=config.max_singletons,
            bridge_budget=config.bridge_budget,
            bridge_quadrature_points=config.bridge_quadrature_points,
            planning_dimensions=dimensions,
            selection_mode=(
                "random" if policy.planning_dimensions is None else "voi"
            ),
            selection_error_bound=config.selection_error_bound,
            planning_max_iterations=config.max_weight_iterations,
        ),
        rng=rng,
    )
    selected = [
        next(candidate for candidate in candidates if candidate.key == key)
        for key in algorithm_result.selected_bridge_keys
    ]
    sources: list[ExperimentData | BridgeCandidate] = [*archive, *selected]
    initial_oracle = _hull_distance(
        target.mechanism.as_array(),
        [source.mechanism.as_array() for source in archive],
    )
    final_oracle = _hull_distance(
        target.mechanism.as_array(),
        [source.mechanism.as_array() for source in sources],
    )
    return BridgeRecord(
        scenario_key=scenario.key,
        scenario_label=scenario.label,
        policy_key=policy.key,
        policy_label=policy.label,
        seed_batch=seed_batch,
        replicate=replicate,
        seed=seed,
        selected_candidate_keys=algorithm_result.selected_bridge_keys,
        selected_candidate_families=algorithm_result.selected_bridge_families,
        evaluation_diameter_path=algorithm_result.partial_diameter_path,
        planning_diameter_path=algorithm_result.planning_diameter_path,
        stopping_reason=algorithm_result.stopping_reason,
        initial_oracle_hull_distance=initial_oracle,
        final_oracle_hull_distance=final_oracle,
        mean_selected_measurement_absolute_error=(
            float(
                np.mean(
                    [
                        abs(candidate.observed_effect - candidate.true_effect)
                        for candidate in selected
                    ]
                )
            )
            if selected
            else 0.0
        ),
        mean_selection_error=algorithm_result.mean_selection_error,
    )


@dataclass(frozen=True)
class BridgeOptimalityRow:
    """Greedy-versus-exhaustive result for one small-library budget."""

    budget: int
    repetitions: int
    exhaustive_sets_per_repetition: int
    greedy_mean_final_diameter: float
    optimal_mean_final_diameter: float
    greedy_mean_shrinkage: float
    optimal_mean_shrinkage: float
    greedy_to_optimal_value_ratio: float | None
    greedy_optimal_selection_rate: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_bridge_optimality_experiment(
    *,
    repetitions: int = 30,
    base_seed: int = 20261121,
    budgets: tuple[int, ...] = (1, 2, 3),
) -> tuple[BridgeOptimalityRow, ...]:
    """Compare causal greedy with ex-post exhaustive subsets on severe mismatch.

    The exhaustive benchmark uses observed outcomes for every enumerated subset
    and is therefore an evaluation oracle, not a deployable policy.
    """

    if repetitions < 2 or not budgets or any(budget < 1 for budget in budgets):
        raise ValueError("repetitions and budgets must be positive.")
    scenario = BridgeScenario("severe", "severe mismatch", 0.80)
    records: dict[int, list[tuple[float, float, float, bool]]] = {
        budget: [] for budget in budgets
    }
    for sequence in np.random.SeedSequence(base_seed).spawn(repetitions):
        seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
        generated = generate_minimal_archive(
            _scenario_dgp_config(SimulationConfig(), scenario), seed=seed
        )
        config = BridgeExperimentConfig(
            repetitions_per_seed=2,
            base_seeds=(base_seed,),
            scenarios=(scenario,),
            bridge_budget=max(budgets),
            selection_error_bound=0.0,
        )
        streams = np.random.SeedSequence(seed).spawn(len(budgets) + 1)
        candidates = _build_bridge_library(
            generated.target, config, np.random.default_rng(streams[0])
        )
        atlas_config = AtlasConfig(scientific_tolerance=0.0, zeta=config.zeta)
        initial_interval = construct_partial_identification_interval(
            generated.archive,
            generated.target,
            atlas_config,
            max_singletons=config.max_singletons,
        )
        if initial_interval.width is None:
            continue
        initial = float(initial_interval.width)
        for stream_index, budget in enumerate(budgets, start=1):
            greedy = run_algorithm1(
                generated.archive,
                generated.target,
                candidates,
                Algorithm1Config(
                    atlas_config=atlas_config,
                    max_singletons=config.max_singletons,
                    bridge_budget=budget,
                    bridge_quadrature_points=config.bridge_quadrature_points,
                    planning_dimensions=(0, 1, 2, 3),
                    selection_error_bound=0.0,
                    planning_max_iterations=config.max_weight_iterations,
                ),
                rng=np.random.default_rng(streams[stream_index]),
            )
            subset_values: list[tuple[float, tuple[str, ...]]] = []
            for subset in combinations(candidates, budget):
                augmented = tuple(generated.archive) + tuple(
                    _candidate_experiment(
                        candidate,
                        generated.target,
                        candidate.observed_effect,
                    )
                    for candidate in subset
                )
                interval = construct_partial_identification_interval(
                    augmented,
                    generated.target,
                    atlas_config,
                    max_singletons=config.max_singletons,
                )
                if interval.width is not None:
                    subset_values.append(
                        (
                            float(interval.width),
                            tuple(candidate.key for candidate in subset),
                        )
                    )
            optimal_final, optimal_keys = min(
                subset_values, key=lambda item: item[0]
            )
            records[budget].append(
                (
                    initial,
                    float(greedy.partial_diameter_path[-1]),
                    optimal_final,
                    frozenset(greedy.selected_bridge_keys)
                    == frozenset(optimal_keys),
                )
            )
    rows = []
    for budget in budgets:
        values = records[budget]
        greedy_shrinkage = float(
            np.mean([initial - greedy for initial, greedy, _, _ in values])
        )
        optimal_shrinkage = float(
            np.mean([initial - optimal for initial, _, optimal, _ in values])
        )
        rows.append(
            BridgeOptimalityRow(
                budget=budget,
                repetitions=len(values),
                exhaustive_sets_per_repetition=int(
                    __import__("math").comb(12, budget)
                ),
                greedy_mean_final_diameter=float(
                    np.mean([item[1] for item in values])
                ),
                optimal_mean_final_diameter=float(
                    np.mean([item[2] for item in values])
                ),
                greedy_mean_shrinkage=greedy_shrinkage,
                optimal_mean_shrinkage=optimal_shrinkage,
                greedy_to_optimal_value_ratio=(
                    greedy_shrinkage / optimal_shrinkage
                    if optimal_shrinkage > 0.0
                    else None
                ),
                greedy_optimal_selection_rate=float(
                    np.mean([item[3] for item in values])
                ),
            )
        )
    return tuple(rows)


def _regularized_hull_weights(
    target: np.ndarray,
    points: np.ndarray,
    standard_errors: np.ndarray,
    variance_penalty: float,
    max_iterations: int,
    tolerance: float,
) -> np.ndarray:
    weights = np.full(len(points), 1.0 / len(points), dtype=float)
    spectral_norm = float(np.linalg.norm(points, ord=2))
    step = 1.0 / max(spectral_norm**2 + variance_penalty * np.max(standard_errors**2), 1e-12)
    current = _weight_objective(weights, target, points, standard_errors, variance_penalty)
    for _ in range(max_iterations):
        residual = weights @ points - target
        gradient = 2.0 * points @ residual + 2.0 * variance_penalty * weights * standard_errors**2
        proposal = _project_to_simplex(weights - step * gradient)
        proposed = _weight_objective(
            proposal,
            target,
            points,
            standard_errors,
            variance_penalty,
        )
        if proposed <= current + 1e-14:
            if np.linalg.norm(proposal - weights) <= tolerance:
                weights = proposal
                break
            weights, current = proposal, proposed
            step = min(step * 1.05, 1.0)
        else:
            step *= 0.5
            if step < 1e-12:
                break
    return weights


def _weight_objective(
    weights: np.ndarray,
    target: np.ndarray,
    points: np.ndarray,
    standard_errors: np.ndarray,
    variance_penalty: float,
) -> float:
    residual = target - weights @ points
    return float(
        residual @ residual
        + variance_penalty * np.sum(weights**2 * standard_errors**2)
    )


def _hull_distance(target: np.ndarray, points: Sequence[np.ndarray]) -> float:
    matrix = np.vstack(points)
    weights = _regularized_hull_weights(
        np.asarray(target, dtype=float),
        matrix,
        np.ones(len(matrix), dtype=float),
        0.0,
        300,
        1e-12,
    )
    return float(np.linalg.norm(weights @ matrix - target))


def _summarize_records(
    records: list[BridgeRecord],
    config: BridgeExperimentConfig,
) -> tuple[BridgeSummaryRow, ...]:
    return tuple(
        _summarize_one(
            scenario,
            policy,
            [
                record
                for record in records
                if record.scenario_key == scenario.key
                and record.policy_key == policy.key
            ],
            config,
        )
        for scenario in config.scenarios
        for policy in config.policies
    )


def _summarize_one(
    scenario: BridgeScenario,
    policy: BridgePolicy,
    records: list[BridgeRecord],
    config: BridgeExperimentConfig,
) -> BridgeSummaryRow:
    if not records:
        raise ValueError("Cannot summarize an empty bridge-policy cell.")
    initial = float(np.mean([record.initial_diameter for record in records]))
    finite_records = [
        record for record in records if record.final_diameter is not None
    ]
    final = (
        float(np.mean([record.final_diameter for record in finite_records]))
        if finite_records
        else None
    )
    seed_finals = [
        float(
            np.mean(
                [
                    record.final_diameter
                    for record in records
                    if record.seed_batch == seed_batch
                    and record.final_diameter is not None
                ]
            )
        )
        for seed_batch in sorted({record.seed_batch for record in records})
        if any(
            record.seed_batch == seed_batch and record.final_diameter is not None
            for record in records
        )
    ]
    selection_errors = [
        record.mean_selection_error
        for record in records
        if record.mean_selection_error is not None
    ]
    return BridgeSummaryRow(
        scenario_key=scenario.key,
        scenario_label=scenario.label,
        policy_key=policy.key,
        policy_label=policy.label,
        repetitions=len(records),
        seed_batches=len(seed_finals),
        bridge_budget=config.bridge_budget,
        completed_repetitions=sum(
            len(record.selected_candidate_keys) == config.bridge_budget
            for record in records
        ),
        budget_completion_rate=float(
            np.mean(
                [
                    len(record.selected_candidate_keys) == config.bridge_budget
                    for record in records
                ]
            )
        ),
        mean_selected_bridge_count=float(
            np.mean([len(record.selected_candidate_keys) for record in records])
        ),
        planning_inconsistency_rate=float(
            np.mean([not record.planning_consistent for record in records])
        ),
        evaluation_inconsistency_rate=float(
            np.mean([not record.evaluation_consistent for record in records])
        ),
        finite_final_diameter_repetitions=len(finite_records),
        mean_initial_diameter=initial,
        mean_final_diameter=final,
        mean_diameter_shrinkage=(initial - final if final is not None else None),
        shrinkage_fraction=(
            (initial - final) / initial
            if final is not None and initial > 0.0
            else None
        ),
        mean_initial_oracle_hull_distance=float(
            np.mean([record.initial_oracle_hull_distance for record in records])
        ),
        mean_final_oracle_hull_distance=float(
            np.mean([record.final_oracle_hull_distance for record in records])
        ),
        mean_selected_measurement_absolute_error=float(
            np.mean(
                [record.mean_selected_measurement_absolute_error for record in records]
            )
        ),
        mean_selection_error=(
            float(np.mean(selection_errors)) if selection_errors else None
        ),
        between_seed_final_diameter_sd=(
            float(np.std(seed_finals, ddof=1)) if len(seed_finals) > 1 else None
        ),
    )
