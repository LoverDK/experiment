# Final simulation summary tables

## Nominal multi-seed benchmark

| estimator | release | MAE | RMSE | coverage | width |
| --- | ---: | ---: | ---: | ---: | ---: |
| atlas | 0.4567 | 0.1111 | 0.1380 | 1.0000 | 3.4043 |
| atlas_no_rejection | 1.0000 | 0.1388 | 0.1705 | 1.0000 | 3.4043 |
| atlas_no_variance_penalty | 0.4400 | 0.1124 | 0.1398 | 1.0000 | 3.4037 |
| atlas_top4_candidates | 0.3233 | 0.1251 | 0.1565 | 1.0000 | 3.7200 |
| semantic_forced | 1.0000 | 0.2241 | 0.2824 | 1.0000 | 4.5340 |
| nearest_semantic | 1.0000 | 0.4557 | 0.5678 | 1.0000 | 4.9600 |
| global_mean | 1.0000 | 0.2816 | 0.3621 | 1.0000 | 5.2776 |

## Failure-boundary comparison

| scenario | policy | release | released MAE | released coverage | above tolerance |
| --- | --- | ---: | ---: | ---: | ---: |
| strong_semantic_mismatch | certified_atlas | 0.0433 | 0.2350 | 1.0000 | 0.0000 |
| strong_semantic_mismatch | no_rejection | 1.0000 | 0.5546 | 1.0000 | 0.9567 |
| strong_semantic_mismatch | understated_smoothness | 1.0000 | 0.5546 | 0.8767 | 0.0000 |
| severe_semantic_mismatch | certified_atlas | 0.0067 | 0.1796 | 1.0000 | 0.0000 |
| severe_semantic_mismatch | no_rejection | 1.0000 | 0.7407 | 1.0000 | 0.9933 |
| severe_semantic_mismatch | understated_smoothness | 1.0000 | 0.7407 | 0.7533 | 0.0000 |
