# Formal experiment tables

All rows pool 300 repetitions from three independent base seeds.

## Table 1. Nominal benchmark

| estimator_key | acceptance_rate | accepted_mae | accepted_rmse | interval_coverage | mean_interval_width |
| --- | --- | --- | --- | --- | --- |
| atlas | 0.4567 | 0.1111 | 0.1380 | 1.0000 | 3.4043 |
| atlas_no_rejection | 1.0000 | 0.1388 | 0.1705 | 1.0000 | 3.4043 |
| atlas_no_variance_penalty | 0.4400 | 0.1124 | 0.1398 | 1.0000 | 3.4037 |
| atlas_top4_candidates | 0.3233 | 0.1251 | 0.1565 | 1.0000 | 3.7200 |
| semantic_forced | 1.0000 | 0.2241 | 0.2824 | 1.0000 | 4.5340 |
| nearest_semantic | 1.0000 | 0.4557 | 0.5678 | 1.0000 | 4.9600 |
| global_mean | 1.0000 | 0.2816 | 0.3621 | 1.0000 | 5.2776 |

## Table 2. ATLAS sensitivity across formal scenarios

| scenario_label | acceptance_rate | acceptance_ci_lower | acceptance_ci_upper | accepted_mae | interval_coverage | between_seed_acceptance_sd |
| --- | --- | --- | --- | --- | --- | --- |
| nominal setting | 0.4567 | 0.4012 | 0.5132 | 0.1111 | 1.0000 | 0.0416 |
| mild semantic mismatch | 0.3933 | 0.3397 | 0.4496 | 0.1262 | 1.0000 | 0.0306 |
| severe semantic mismatch | 0.2767 | 0.2291 | 0.3299 | 0.1568 | 1.0000 | 0.0503 |
| larger hidden-moderator uncertainty | 0.0000 | 0.0000 | 0.0126 | NA | 1.0000 | 0.0000 |
| small experiments | 0.2300 | 0.1860 | 0.2809 | 0.1219 | 1.0000 | 0.0361 |
| large experiments | 0.4967 | 0.4405 | 0.5529 | 0.1119 | 1.0000 | 0.0513 |

## Table 3. Nominal ablations

| estimator_key | acceptance_rate | accepted_mae | accepted_bias | interval_coverage | mean_certificate_radius |
| --- | --- | --- | --- | --- | --- |
| atlas | 0.4567 | 0.1111 | -0.0985 | 1.0000 | 1.7021 |
| atlas_no_rejection | 1.0000 | 0.1388 | -0.1295 | 1.0000 | 1.7021 |
| atlas_no_variance_penalty | 0.4400 | 0.1124 | -0.0991 | 1.0000 | 1.7019 |
| atlas_top4_candidates | 0.3233 | 0.1251 | -0.0775 | 1.0000 | 1.8600 |

Rows with an empty accepted MAE correspond to complete rejection, not a failed run.
