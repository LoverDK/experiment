"""Evaluation-only baselines that are forbidden in deployable workflows."""

from __future__ import annotations

from dataclasses import replace
from typing import Sequence

from .dgp import ExperimentData
from .methods import AtlasConfig, AtlasResult, fit_no_rejection_atlas


def fit_oracle_latent_support(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: AtlasConfig | None = None,
) -> AtlasResult:
    """Use true simulated mechanisms in place of public representations.

    This is an evaluation-only upper reference. The archive effect estimates,
    standard errors, design filter, simplex constraints, variance penalty, and
    certificate protocol remain unchanged. Only ``r(e)`` is replaced by the
    unavailable latent coordinate ``m(e)``. Rejection is disabled so the
    comparison isolates representation quality on the common target sample.
    """

    oracle_config = replace(
        config or AtlasConfig(),
        representation_dimensions=None,
    )
    oracle_archive = tuple(
        replace(
            experiment,
            observed_representation=experiment.mechanism.as_array(),
        )
        for experiment in archive
    )
    oracle_target = replace(
        target,
        observed_representation=target.mechanism.as_array(),
    )
    result = fit_no_rejection_atlas(
        oracle_archive,
        oracle_target,
        oracle_config,
    )
    return replace(result, method="oracle_latent_support")
