# Certificate calibration and failure-boundary tables

All rows pool 300 repetitions from three independent base seeds.

## Table 1. Certified ATLAS calibration

| scenario_label | release_rate | mean_raw_mae | released_mae | overall_interval_coverage | mean_certificate_radius |
| --- | --- | --- | --- | --- | --- |
| nominal certified setting | 0.4300 | 0.1453 | 0.1189 | 1.0000 | 1.6927 |
| heterogeneous archive hidden radii | 0.0300 | 0.1835 | 0.1647 | 1.0000 | 2.2577 |
| strong semantic mismatch | 0.0433 | 0.5546 | 0.2350 | 1.0000 | 3.1617 |
| severe semantic mismatch | 0.0067 | 0.7407 | 0.1796 | 1.0000 | 3.9968 |

## Table 2. Strong-mismatch release policies

| scenario_label | policy_key | release_rate | released_mae | released_interval_coverage | released_interval_uncovered_rate | released_above_tolerance_rate |
| --- | --- | --- | --- | --- | --- | --- |
| strong semantic mismatch | certified_atlas | 0.0433 | 0.2350 | 1.0000 | 0.0000 | 0.0000 |
| strong semantic mismatch | no_rejection | 1.0000 | 0.5546 | 1.0000 | 0.0000 | 0.9567 |
| strong semantic mismatch | understated_smoothness | 1.0000 | 0.5546 | 0.8767 | 0.1233 | 0.0000 |
| severe semantic mismatch | certified_atlas | 0.0067 | 0.1796 | 1.0000 | 0.0000 | 0.0000 |
| severe semantic mismatch | no_rejection | 1.0000 | 0.7407 | 1.0000 | 0.0000 | 0.9933 |
| severe semantic mismatch | understated_smoothness | 1.0000 | 0.7407 | 0.7533 | 0.2467 | 0.0000 |

## Table 3. Heterogeneous hidden-radius scenario

| policy_key | release_rate | released_mae | released_interval_coverage | mean_certificate_radius |
| --- | --- | --- | --- | --- |
| certified_atlas | 0.0300 | 0.1647 | 1.0000 | 2.2577 |
| no_rejection | 1.0000 | 0.1835 | 1.0000 | 2.2577 |
| understated_smoothness | 1.0000 | 0.1835 | 1.0000 | 0.9792 |

The understated-smoothness policy intentionally uses false bounds and is
included to demonstrate calibration failure, not as a valid estimator.
