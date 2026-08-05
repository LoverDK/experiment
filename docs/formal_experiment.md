# Stage 5: multi-seed formal benchmark and ablations

This stage replaces the single screening seed with a formal pooled protocol.
Six scenarios are evaluated with three independent base seeds and 100
repetitions per seed. Each scenario-estimator row therefore pools 300 targets,
while the seed-level table preserves the three independent batch estimates.

## Formal scenarios

| key | changed factor |
| --- | --- |
| nominal | shift 0, hidden radius 0.20, n = 400, tolerance 1.65 |
| semantic_mismatch_010 | semantic shift fraction 0.10 |
| semantic_mismatch_025 | semantic shift fraction 0.25 |
| hidden_radius_040 | hidden moderator radius 0.40 |
| sample_size_100 | 100 units per experiment |
| sample_size_1000 | 1000 units per experiment |

The same child seeds are reused across scenarios. This creates paired
mechanism draws while changing only the scenario factor. Within every target
draw, all estimators receive exactly the same archive and target records.

## Methods and ablations

- atlas: the full rejectable method;
- atlas_no_rejection: identical weights and certificate, but the point estimate
  is always released;
- atlas_no_variance_penalty: set lambda_sigma to zero in weight learning;
- atlas_top4_candidates: restrict retrieval to the four closest compatible
  experiments;
- semantic_forced, nearest_semantic, and global_mean: comparison baselines.

A no-hidden-penalty weight ablation is intentionally omitted from this DGP.
Every archive experiment currently has the same moderator radius, so the
weighted hidden-radius term is constant on the simplex and removing it would
be algebraically identical. A meaningful version requires heterogeneous
archive-specific moderator radii and belongs in the next robustness stage.

## Reported uncertainty

The pooled table reports acceptance, a Wilson 95 percent Monte Carlo interval
for the acceptance rate, accepted-point MAE and its Monte Carlo
standard error, RMSE, bias, sign accuracy, interval coverage, interval width,
and mean certificate radius. It also reports the standard deviation of
acceptance and MAE across the three base-seed batches.

## Current findings

In the nominal setting, full ATLAS accepts 0.4567 of targets and has accepted
MAE 0.1111. The no-rejection version has MAE 0.1388, while semantic forced,
nearest semantic, and global mean have MAE 0.2241, 0.4557, and 0.2816.

Increasing semantic mismatch from 0 to 0.25 lowers ATLAS acceptance from
0.4567 to 0.2767 and raises accepted MAE from 0.1111 to 0.1568. The hidden
radius 0.40 scenario is completely rejected. Increasing sample size from 100
to 1000 raises acceptance from 0.2300 to 0.4967.

Removing variance regularization has only a small effect in the nominal DGP:
acceptance changes from 0.4567 to 0.4400 and accepted MAE from 0.1111 to
0.1124. Restricting retrieval to four candidates is more consequential:
acceptance falls to 0.3233 and accepted MAE rises to 0.1251.

All certified intervals cover the synthetic truth in these runs. This is
consistent with conservative certificates, but it also motivates a dedicated
calibration stress test rather than treating 1.000 coverage as automatically
optimal.

## Reproducible outputs

- results/formal_experiment_summary.csv: pooled 42-row result table;
- results/formal_experiment_seed_summary.csv: 126 seed-specific rows;
- results/formal_experiment_metadata.json: exact protocol;
- results/tables/formal_experiment_tables.md: three paper-facing tables;
- results/figures/formal_experiment_overview.png: benchmark overview.

Run:

    python scripts/run_formal_experiment.py
