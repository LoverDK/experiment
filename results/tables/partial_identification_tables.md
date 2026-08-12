# Partial-identification experiment tables

All rows pool 300 repetitions from three independent base seeds.
The interval intersects six simultaneously certified weight-specific
intervals: support-optimized, compatible-uniform, and four nearest
design-compatible semantic singletons.

## Table 1. Theorem 5.4 fallback after failed composition

| scenario_label | rejection_rate | partial_id_nonempty_rate | partial_id_coverage | partial_id_coverage_on_rejected | mean_partial_id_width_on_rejected | mean_reference_width_on_rejected | mean_width_reduction_fraction_on_rejected | mean_oracle_hull_distance | mean_nonidentification_separation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| nominal support | 0.5167 | 1.0000 | 1.0000 | 1.0000 | 3.6462 | 3.7518 | 0.0274 | 0.0000 | 0.0000 |
| moderate semantic mismatch | 0.7767 | 1.0000 | 1.0000 | 1.0000 | 4.0945 | 4.3425 | 0.0514 | 0.1325 | 0.3459 |
| strong semantic mismatch | 0.9733 | 1.0000 | 1.0000 | 1.0000 | 5.6743 | 6.4837 | 0.1143 | 0.6471 | 1.6890 |
| severe semantic mismatch | 0.9900 | 1.0000 | 1.0000 | 1.0000 | 7.0760 | 8.0676 | 0.1125 | 0.9974 | 2.5976 |

Oracle hull distance and nonidentification separation are evaluation
metrics only. They are not supplied to ATLAS or the interval builder.
