# Theorem 5.6 bridge-design experiment tables

Each row pools 300 repetitions from three independent base seeds.
The diameter is the Theorem 5.4 partial-identification intersection
evaluated using the full observed representation.

## Table 1. Bridge value by selection policy

| scenario_key | policy_key | bridge_budget | budget_completion_rate | mean_selected_bridge_count | planning_inconsistency_rate | evaluation_inconsistency_rate | mean_initial_diameter | mean_final_diameter | mean_diameter_shrinkage | shrinkage_fraction | mean_initial_oracle_hull_distance | mean_final_oracle_hull_distance | between_seed_final_diameter_sd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supported | causal_greedy | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 3.3502 | 2.3093 | 1.0410 | 0.3107 | 0.0000 | 0.0000 | 0.0128 |
| supported | semantic_greedy | 4 | 0.9967 | 3.9900 | 0.0067 | 0.0000 | 3.3502 | 2.7790 | 0.5712 | 0.1705 | 0.0000 | 0.0000 | 0.0418 |
| supported | random | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 3.3502 | 2.6373 | 0.7129 | 0.2128 | 0.0000 | 0.0000 | 0.0132 |
| moderate | causal_greedy | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 3.7867 | 2.0674 | 1.7193 | 0.4540 | 0.1246 | 0.0052 | 0.0073 |
| moderate | semantic_greedy | 4 | 0.9833 | 3.9667 | 0.0200 | 0.0000 | 3.7867 | 2.6577 | 1.1290 | 0.2982 | 0.1246 | 0.0076 | 0.0407 |
| moderate | random | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 3.7867 | 2.5285 | 1.2583 | 0.3323 | 0.1246 | 0.0066 | 0.0152 |
| strong | causal_greedy | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 5.5042 | 1.8620 | 3.6422 | 0.6617 | 0.6446 | 0.0200 | 0.0061 |
| strong | semantic_greedy | 4 | 0.9433 | 3.8933 | 0.0600 | 0.0000 | 5.5042 | 2.4832 | 3.0210 | 0.5489 | 0.6446 | 0.0300 | 0.0145 |
| strong | random | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 5.5042 | 2.3848 | 3.1195 | 0.5667 | 0.6446 | 0.0314 | 0.0473 |
| severe | causal_greedy | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 6.9423 | 1.8772 | 5.0651 | 0.7296 | 1.0015 | 0.0316 | 0.0081 |
| severe | semantic_greedy | 4 | 0.9667 | 3.9300 | 0.0367 | 0.0000 | 6.9423 | 2.3309 | 4.6114 | 0.6642 | 1.0015 | 0.0274 | 0.0206 |
| severe | random | 4 | 1.0000 | 4.0000 | 0.0000 | 0.0000 | 6.9423 | 2.3167 | 4.6256 | 0.6663 | 1.0015 | 0.0401 | 0.0454 |

The causal greedy policy plans with all four public coordinates; the
semantic policy plans with only (s1, s2). Oracle hull distance and
bridge measurement error are not supplied to either policy.

## Table 2. Interpretation

- `mean_diameter_shrinkage` is empirical Definition 5.2 bridge value
  among paths whose evaluation intersection remains nonempty.
- `planning_inconsistency_rate` and `evaluation_inconsistency_rate`
  report empty intersections as Lemma 5.1 diagnostics, never as zero
  diameter or successful shrinkage.
- `mean_final_oracle_hull_distance` is an evaluation-only support check.
- The experiment compares policies; it does not prove weak submodularity.
