# Final simulation summary tables

## Nominal multi-seed benchmark

| estimator | release | MAE | RMSE | coverage | width |
| --- | ---: | ---: | ---: | ---: | ---: |
| atlas | 0.4633 | 0.1109 | 0.1375 | 1.0000 | 3.3391 |
| atlas_no_rejection | 1.0000 | 0.1387 | 0.1703 | 1.0000 | 3.3391 |
| atlas_no_variance_penalty | 0.4400 | 0.1124 | 0.1398 | 1.0000 | 3.3390 |
| atlas_top4_candidates | 0.3200 | 0.1234 | 0.1545 | 1.0000 | 3.6261 |
| semantic_forced | 1.0000 | 0.2241 | 0.2824 | 1.0000 | 4.4769 |
| nearest_semantic | 1.0000 | 0.4557 | 0.5678 | 1.0000 | 4.8087 |
| global_mean | 1.0000 | 0.2816 | 0.3621 | 1.0000 | 5.2241 |

## Failure-boundary comparison

| scenario | policy | release | released MAE | released coverage | above tolerance |
| --- | --- | ---: | ---: | ---: | ---: |
| strong_semantic_mismatch | certified_atlas | 0.0433 | 0.2354 | 1.0000 | 0.0000 |
| strong_semantic_mismatch | no_rejection | 1.0000 | 0.5546 | 1.0000 | 0.9567 |
| strong_semantic_mismatch | understated_smoothness | 1.0000 | 0.5546 | 0.8333 | 0.0000 |
| severe_semantic_mismatch | certified_atlas | 0.0067 | 0.1795 | 1.0000 | 0.0000 |
| severe_semantic_mismatch | no_rejection | 1.0000 | 0.7408 | 1.0000 | 0.9933 |
| severe_semantic_mismatch | understated_smoothness | 1.0000 | 0.7408 | 0.7233 | 0.0000 |
