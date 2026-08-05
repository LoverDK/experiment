"""Synthetic data generators for Causal ATLAS experiments."""

from .dgp import (
    EFFECT_CURVATURE_BOUND,
    EFFECT_LIPSCHITZ_BOUND,
    HIDDEN_MODERATOR_LIPSCHITZ_BOUND,
    DesignProfile,
    ExperimentData,
    GeneratedArchive,
    Mechanism,
    SimulationConfig,
    assert_minimal_assumptions,
    effect_gradient,
    effect_hessian,
    effect_surface,
    generate_minimal_archive,
    minimal_assumption_report,
)

__all__ = [
    "EFFECT_CURVATURE_BOUND",
    "EFFECT_LIPSCHITZ_BOUND",
    "HIDDEN_MODERATOR_LIPSCHITZ_BOUND",
    "DesignProfile",
    "ExperimentData",
    "GeneratedArchive",
    "Mechanism",
    "SimulationConfig",
    "assert_minimal_assumptions",
    "effect_gradient",
    "effect_hessian",
    "effect_surface",
    "generate_minimal_archive",
    "minimal_assumption_report",
]
