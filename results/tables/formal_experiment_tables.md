# Formal experiment tables

All rows pool 300 repetitions from three independent base seeds.

## Table 1. Nominal benchmark

| estimator_key | acceptance_rate | accepted_mae | accepted_rmse | interval_coverage | mean_interval_width |
| --- | --- | --- | --- | --- | --- |
| atlas | 0.4633 | 0.1109 | 0.1375 | 1.0000 | 3.3391 |
| atlas_no_rejection | 1.0000 | 0.1387 | 0.1703 | 1.0000 | 3.3391 |
| atlas_no_variance_penalty | 0.4400 | 0.1124 | 0.1398 | 1.0000 | 3.3390 |
| atlas_top4_candidates | 0.3200 | 0.1234 | 0.1545 | 1.0000 | 3.6261 |
| semantic_forced | 1.0000 | 0.2241 | 0.2824 | 1.0000 | 4.4769 |
| nearest_semantic | 1.0000 | 0.4557 | 0.5678 | 1.0000 | 4.8087 |
| global_mean | 1.0000 | 0.2816 | 0.3621 | 1.0000 | 5.2241 |

## Table 2. ATLAS sensitivity across formal scenarios

| scenario_label | acceptance_rate | acceptance_ci_lower | acceptance_ci_upper | accepted_mae | interval_coverage | between_seed_acceptance_sd |
| --- | --- | --- | --- | --- | --- | --- |
| nominal setting | 0.4633 | 0.4077 | 0.5199 | 0.1109 | 1.0000 | 0.0379 |
| mild semantic mismatch | 0.3900 | 0.3365 | 0.4463 | 0.1257 | 1.0000 | 0.0265 |
| severe semantic mismatch | 0.2833 | 0.2353 | 0.3368 | 0.1581 | 1.0000 | 0.0404 |
| larger hidden-moderator uncertainty | 0.0000 | 0.0000 | 0.0126 | NA | 1.0000 | 0.0000 |
| small experiments | 0.2300 | 0.1860 | 0.2809 | 0.1229 | 1.0000 | 0.0458 |
| large experiments | 0.5000 | 0.4438 | 0.5562 | 0.1127 | 1.0000 | 0.0529 |

## Table 3. Nominal ablations

| estimator_key | acceptance_rate | accepted_mae | accepted_bias | interval_coverage | mean_certificate_radius |
| --- | --- | --- | --- | --- | --- |
| atlas | 0.4633 | 0.1109 | -0.0984 | 1.0000 | 1.7016 |
| atlas_no_rejection | 1.0000 | 0.1387 | -0.1293 | 1.0000 | 1.7016 |
| atlas_no_variance_penalty | 0.4400 | 0.1124 | -0.0991 | 1.0000 | 1.7019 |
| atlas_top4_candidates | 0.3200 | 0.1234 | -0.0753 | 1.0000 | 1.8601 |

Rows with an empty accepted MAE correspond to complete rejection, not a failed run.
