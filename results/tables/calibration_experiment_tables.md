# Certificate calibration and failure-boundary tables

All rows pool 300 repetitions from three independent base seeds.

## Table 1. Certified ATLAS calibration

| scenario_label | release_rate | mean_raw_mae | released_mae | overall_interval_coverage | mean_certificate_radius |
| --- | --- | --- | --- | --- | --- |
| nominal certified setting | 0.4267 | 0.1451 | 0.1183 | 1.0000 | 1.6927 |
| heterogeneous archive hidden radii | 0.0300 | 0.1835 | 0.1649 | 1.0000 | 2.2576 |
| strong semantic mismatch | 0.0433 | 0.5546 | 0.2354 | 1.0000 | 3.1615 |
| severe semantic mismatch | 0.0067 | 0.7408 | 0.1795 | 1.0000 | 3.9966 |

## Table 2. Strong-mismatch release policies

| scenario_label | policy_key | release_rate | released_mae | released_interval_coverage | released_interval_uncovered_rate | released_above_tolerance_rate |
| --- | --- | --- | --- | --- | --- | --- |
| strong semantic mismatch | certified_atlas | 0.0433 | 0.2354 | 1.0000 | 0.0000 | 0.0000 |
| strong semantic mismatch | no_rejection | 1.0000 | 0.5546 | 1.0000 | 0.0000 | 0.9567 |
| strong semantic mismatch | understated_smoothness | 1.0000 | 0.5546 | 0.8333 | 0.1667 | 0.0000 |
| severe semantic mismatch | certified_atlas | 0.0067 | 0.1795 | 1.0000 | 0.0000 | 0.0000 |
| severe semantic mismatch | no_rejection | 1.0000 | 0.7408 | 1.0000 | 0.0000 | 0.9933 |
| severe semantic mismatch | understated_smoothness | 1.0000 | 0.7408 | 0.7233 | 0.2767 | 0.0000 |

## Table 3. Heterogeneous hidden-radius scenario

| policy_key | release_rate | released_mae | released_interval_coverage | mean_certificate_radius |
| --- | --- | --- | --- | --- |
| certified_atlas | 0.0300 | 0.1649 | 1.0000 | 2.2576 |
| no_rejection | 1.0000 | 0.1835 | 1.0000 | 2.2576 |
| understated_smoothness | 1.0000 | 0.1835 | 1.0000 | 0.9791 |

The understated-smoothness policy intentionally uses false bounds and is
included to demonstrate calibration failure, not as a valid estimator.
