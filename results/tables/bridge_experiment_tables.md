# Theorem 5.6 bridge-design experiment tables

Each row pools 300 repetitions from three independent base seeds.
The diameter is a support, curvature, hidden-moderator, and statistical
certificate proxy evaluated using the full observed representation.

## Table 1. Bridge value by selection policy

| scenario_key | policy_key | bridge_budget | mean_initial_diameter | mean_final_diameter | mean_diameter_shrinkage | shrinkage_fraction | mean_initial_oracle_hull_distance | mean_final_oracle_hull_distance | between_seed_final_diameter_sd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supported | causal_greedy | 4 | 3.3559 | 2.5332 | 0.8228 | 0.2452 | 0.0000 | 0.0000 | 0.0325 |
| supported | semantic_greedy | 4 | 3.3559 | 2.8771 | 0.4788 | 0.1427 | 0.0000 | 0.0000 | 0.0378 |
| supported | random | 4 | 3.3559 | 2.8250 | 0.5309 | 0.1582 | 0.0000 | 0.0000 | 0.0235 |
| moderate | causal_greedy | 4 | 3.9344 | 2.0668 | 1.8676 | 0.4747 | 0.1246 | 0.0051 | 0.0148 |
| moderate | semantic_greedy | 4 | 3.9344 | 2.7369 | 1.1975 | 0.3044 | 0.1246 | 0.0100 | 0.0252 |
| moderate | random | 4 | 3.9344 | 2.6335 | 1.3009 | 0.3307 | 0.1246 | 0.0062 | 0.0330 |
| strong | causal_greedy | 4 | 6.1000 | 1.7765 | 4.3236 | 0.7088 | 0.6446 | 0.0148 | 0.0035 |
| strong | semantic_greedy | 4 | 6.1000 | 2.4289 | 3.6711 | 0.6018 | 0.6446 | 0.0271 | 0.0444 |
| strong | random | 4 | 6.1000 | 2.3967 | 3.7033 | 0.6071 | 0.6446 | 0.0306 | 0.0548 |
| severe | causal_greedy | 4 | 7.0338 | 1.7817 | 5.2521 | 0.7467 | 1.0015 | 0.0153 | 0.0090 |
| severe | semantic_greedy | 4 | 7.0338 | 2.1808 | 4.8529 | 0.6899 | 1.0015 | 0.0155 | 0.0044 |
| severe | random | 4 | 7.0338 | 2.3104 | 4.7234 | 0.6715 | 1.0015 | 0.0389 | 0.0521 |

The causal greedy policy plans with all four public coordinates; the
semantic policy plans with only (s1, s2). Oracle hull distance and
bridge measurement error are not supplied to either policy.

## Table 2. Interpretation

- `mean_diameter_shrinkage` is the empirical bridge value in the
  restricted certificate proxy.
- `mean_final_oracle_hull_distance` is an evaluation-only support check.
- The experiment compares policies; it does not prove weak submodularity.
