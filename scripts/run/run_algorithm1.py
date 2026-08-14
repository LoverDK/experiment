"""Run one visible rejected-target path through every branch of Algorithm 1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim import (
    Algorithm1Config,
    AtlasConfig,
    BridgeCandidate,
    Mechanism,
    SimulationConfig,
    effect_surface,
    generate_minimal_archive,
    run_algorithm1,
)


def _bridge_library(target) -> tuple[BridgeCandidate, ...]:
    offsets = (
        ("near_target", (0.05, -0.04, 0.04, -0.03)),
        ("semantic_decoy", (0.02, 0.02, 0.60, -0.55)),
        ("mixed", (-0.25, 0.20, -0.20, 0.18)),
    )
    rng = np.random.default_rng(20260812)
    candidates = []
    for key, offset in offsets:
        representation = np.clip(
            target.observed_representation + np.asarray(offset, dtype=float),
            -1.0,
            1.0,
        )
        mechanism = Mechanism.from_array(representation)
        true_effect = effect_surface(mechanism)
        candidates.append(
            BridgeCandidate(
                key=key,
                family=key,
                mechanism=mechanism,
                observed_representation=representation,
                standard_error=0.10,
                moderator_sensitivity_radius=target.moderator_sensitivity_radius,
                true_effect=true_effect,
                observed_effect=float(true_effect + 0.10 * rng.normal()),
            )
        )
    return tuple(candidates)


def main() -> None:
    generated = generate_minimal_archive(
        SimulationConfig(target_shift_fraction=0.60),
        seed=20260812,
    )
    result = run_algorithm1(
        generated.archive,
        generated.target,
        _bridge_library(generated.target),
        Algorithm1Config(
            atlas_config=AtlasConfig(scientific_tolerance=0.0),
            bridge_budget=2,
        ),
        rng=np.random.default_rng(20260812),
    )
    initial = result.partial_interval
    updated = result.updated_partial_interval
    output = {
        "branch": result.branch,
        "certificate_radius": result.atlas_result.certificate.radius,
        "point_estimate": result.atlas_result.point_estimate,
        "honest_interval": list(result.atlas_result.interval),
        "initial_partial_id": (
            [initial.interval_lower, initial.interval_upper]
            if initial is not None
            else None
        ),
        "selected_bridges": list(result.selected_bridge_keys),
        "stopping_reason": result.stopping_reason,
        "marginal_values": list(result.selected_bridge_marginal_values),
        "partial_id_diameter_path": list(result.partial_diameter_path),
        "updated_partial_id": (
            [updated.interval_lower, updated.interval_upper]
            if updated is not None
            else None
        ),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
