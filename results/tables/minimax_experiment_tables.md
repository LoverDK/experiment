# Theorem 5.5 minimax experiment tables

Each row pools 300 repetitions from three independent base seeds.
The representative estimator is the inverse-variance archive mean.

## Table 1. Constructive lower-bound components

| scenario_key | hull_distance | archive_standard_error | geometric_scale | geometric_lower_bound | information_scale | statistical_lower_bound | combined_lower_bound |
| --- | --- | --- | --- | --- | --- | --- | --- |
| d000_precise | 0.0000 | 0.3500 | 0.0000 | 0.0000 | 0.1237 | 0.0116 | 0.0116 |
| d000_noisy | 0.0000 | 1.2000 | 0.0000 | 0.0000 | 0.4243 | 0.0398 | 0.0398 |
| d025_precise | 0.2500 | 0.3500 | 0.6525 | 0.1631 | 0.1237 | 0.0116 | 0.1631 |
| d025_noisy | 0.2500 | 1.2000 | 0.6525 | 0.1631 | 0.4243 | 0.0398 | 0.1631 |
| d060_precise | 0.6000 | 0.3500 | 1.5660 | 0.3915 | 0.1237 | 0.0116 | 0.3915 |
| d060_noisy | 0.6000 | 1.2000 | 1.5660 | 0.3915 | 0.4243 | 0.0398 | 0.3915 |
| d100_precise | 1.0000 | 0.3500 | 2.6100 | 0.6525 | 0.1237 | 0.0116 | 0.6525 |
| d100_noisy | 1.0000 | 1.2000 | 2.6100 | 0.6525 | 0.4243 | 0.0398 | 0.6525 |

## Table 2. Representative-estimator worst-case absolute risk

| scenario_key | empirical_geometric_worst_mae | empirical_statistical_worst_mae | empirical_worst_case_mae | analytic_worst_case_mae | empirical_to_lower_bound_ratio | between_seed_worst_case_mae_sd |
| --- | --- | --- | --- | --- | --- | --- |
| d000_precise | 0.0959 | 0.0989 | 0.0989 | 0.0987 | 8.5243 | 0.0037 |
| d000_noisy | 0.3287 | 0.3391 | 0.3391 | 0.3385 | 8.5243 | 0.0125 |
| d025_precise | 0.1739 | 0.0989 | 0.1739 | 0.1740 | 1.0659 | 0.0050 |
| d025_noisy | 0.3647 | 0.3391 | 0.3647 | 0.3632 | 2.2358 | 0.0115 |
| d060_precise | 0.3918 | 0.0989 | 0.3918 | 0.3916 | 1.0008 | 0.0047 |
| d060_noisy | 0.4767 | 0.3391 | 0.4767 | 0.4732 | 1.2175 | 0.0193 |
| d100_precise | 0.6528 | 0.0989 | 0.6528 | 0.6525 | 1.0005 | 0.0047 |
| d100_noisy | 0.6741 | 0.3391 | 0.6741 | 0.6753 | 1.0331 | 0.0160 |

The geometric and statistical rows are the two independent proof
submodels. Their maximum is the reported constructive lower bound.
