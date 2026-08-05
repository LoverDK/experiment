# Stage 6: certificate calibration and failure boundaries

This experiment tests whether rejection and interval coverage behave as the
certificate claims. It uses four scenarios, three independent base seeds, and
100 repetitions per seed. Every scenario-policy row therefore pools 300 target
experiments. Policies are always evaluated on the same generated records.

## Scenarios

| scenario | change |
| --- | --- |
| nominal | original DGP and certified bounds |
| heterogeneous hidden radii | archive sensitivity radii range from 0.20 to 0.60 |
| strong semantic mismatch | target shift fraction 0.60 |
| severe semantic mismatch | target shift fraction 0.80 |

The heterogeneous-radius setting preserves every proxy-compatible h set: the
target radius remains 0.20 and archive radii increase from 0.20 to 0.60. The
observable proxy noise remains bounded by 0.10. Thus this is a conservative
certificate stress test, not an assumption violation.

## Policies

- certified_atlas: uses the analytic L = 2.61 and H = 1.80 bounds and the
  reject rule with scientific tolerance 1.65;
- no_rejection: uses the same learned weights and certified interval but always
  releases the point estimate;
- understated_smoothness: intentionally supplies false L = 0.20 and H = 0.05
  bounds to the method. It is included only to show what happens when a
  certificate is invalid.

## Metrics

Besides release rate and mean absolute error, this stage records:

- released_interval_coverage: empirical coverage among released point
  predictions;
- released_interval_uncovered_rate: one minus that coverage;
- released_above_tolerance_rate: proportion of released points whose
  certificate radius exceeds the scientific tolerance;
- overall_interval_coverage: coverage before the accept/reject decision.

The distinction is important. A no-rejection estimator can still have a
covering interval while releasing a point whose certificate says it is not
scientifically reliable.

## Results

With correct bounds, ATLAS releases 0.4300 in the nominal setting, 0.0300 with
heterogeneous hidden radii, 0.0433 under strong mismatch, and 0.0067 under
severe mismatch. Its overall certified interval coverage is 1.0000 in every
case.

Under strong and severe mismatch, no_rejection releases every point even
though 0.9567 and 0.9933 of those released points have certificate radius
above tolerance. Correct ATLAS avoids those releases.

The false understated-smoothness policy also releases every point, but its
released interval coverage falls to 0.8767 under strong mismatch and 0.7533
under severe mismatch. This is the intended failure boundary: the DGP remains
valid, but the method was given incorrect smoothness constants.

## Outputs

- results/calibration_experiment_summary.csv: pooled 12-row table;
- results/calibration_experiment_seed_summary.csv: 36 seed-specific rows;
- results/calibration_experiment_metadata.json: full configuration;
- results/tables/calibration_experiment_tables.md: report tables;
- results/figures/calibration_experiment_overview.png: release and coverage
  comparison.

Run:

    python scripts/run_calibration_experiment.py
