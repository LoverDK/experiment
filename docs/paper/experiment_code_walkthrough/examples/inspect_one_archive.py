"""A read-only, one-archive teaching example; see chapter 10 for each step."""
from dataclasses import asdict, replace
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from causal_atlas_sim.dgp import SimulationConfig, generate_minimal_archive
from causal_atlas_sim.methods import AtlasConfig, fit_causal_atlas
from causal_atlas_sim.algorithm1 import Algorithm1Config, run_algorithm1


def main():
    config = SimulationConfig()
    generated = generate_minimal_archive(config, seed=20260805)
    source = generated.archive[0]
    shapes = {
        "archive_count": len(generated.archive),
        "unit_covariates": list(source.x.shape),
        "treatment": list(source.treatment.shape),
        "aipw_scores": list(source.aipw_scores.shape),
        "public_representation": list(source.observed_representation.shape),
    }
    print("STEP 1: data shapes")
    print(json.dumps(shapes, indent=2))

    mean_score = float(source.aipw_scores.mean())
    score_se = float(source.aipw_scores.std(ddof=1) / np.sqrt(source.n_units))
    np.testing.assert_allclose(mean_score, source.estimated_effect)
    np.testing.assert_allclose(score_se, source.standard_error_certificate)
    print("STEP 2: source estimate and SE", mean_score, score_se)

    # Poison evaluation fields before passing the target into the estimator.
    blind = replace(generated.target, true_effect=float("nan"),
                    estimated_effect=float("nan"), standard_error_certificate=float("nan"))
    result = fit_causal_atlas(generated.archive, blind, AtlasConfig())
    effects = np.array([e.estimated_effect for e in generated.archive])
    manual_point = float(result.weights @ effects)
    np.testing.assert_allclose(result.weights.sum(), 1)
    assert np.all(result.weights >= -1e-10)
    np.testing.assert_allclose(manual_point, result.raw_point_estimate)
    certificate = asdict(result.certificate)
    manual_radius = sum(value for key, value in certificate.items() if key != "radius")
    np.testing.assert_allclose(manual_radius, result.certificate.radius)
    print("STEP 3: candidate indices", result.candidate_indices)
    print("STEP 3: full weights", result.weights)
    print("STEP 3: certificate", json.dumps(certificate, indent=2))
    print("STEP 3: raw / released / accepted", result.raw_point_estimate,
          result.point_estimate, result.accepted)
    print("STEP 3: evaluation truth and error", generated.target.true_effect,
          abs(manual_point - generated.target.true_effect))

    # A zero tolerance routes this teaching draw into the rejection branch.
    rejected = run_algorithm1(generated.archive, blind,
                             config=Algorithm1Config(atlas_config=AtlasConfig(scientific_tolerance=0)))
    interval = rejected.partial_interval
    assert interval is not None
    np.testing.assert_allclose(interval.interval_lower,
                               max(c-r for c, r in zip(interval.centers, interval.radii)))
    np.testing.assert_allclose(interval.interval_upper,
                               min(c+r for c, r in zip(interval.centers, interval.radii)))
    print("STEP 4: PI weight labels", interval.weight_labels)
    print("STEP 4: component zeta", interval.component_zeta)
    print("STEP 4: PI lower / upper / width", interval.interval_lower,
          interval.interval_upper, interval.width)
    print("STEP 4: truth included", interval.contains(generated.target.true_effect))
    print("This is one teaching draw. No experiment result or paper file was written.")


if __name__ == "__main__":
    main()
