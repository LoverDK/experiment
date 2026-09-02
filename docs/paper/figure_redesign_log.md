# Figure 2--5 redesign record

This record freezes the paper-facing figure assignment after the final candidate
selection pass. It does not alter a simulation protocol, random seed, or numeric
result. `scripts/build/build_paper_figures.py` reads the committed CSV/JSON files
and recreates every asset listed below.

## Main figures

| Figure | Main question | Panels | Source records |
| --- | --- | --- | --- |
| Figure 2 | Why causal support is more informative than semantic proximity | semantic-neighbor mechanism sketch; six-method error ECDF; 5x5 representation-sensitivity heatmap; hidden-shift slice with representation advantage and release rate | `certificate_diagnostics_summary.csv`, `representation_sensitivity_summary.csv` |
| Figure 3 | Why certification needs selective release and honest uncertainty | risk--coverage; coverage--width; released/rejected certificate components; mismatch failure boundary | `risk_coverage_summary.csv`, `calibration_curve_summary.csv`, `calibration_experiment_summary.csv`, `certificate_diagnostics_summary.csv` |
| Figure 4 | How rejection leads to partial identification and bridge design | PI diameter versus evaluation-only support stress; severe-scenario budget paths; evaluation-only true-mechanism hull distance; greedy/ex-post exhaustive value ratio | `partial_identification_summary.csv`, `bridge_budget_path_summary.csv`, `bridge_experiment_summary.csv`, `bridge_optimality_summary.csv` |
| Figure 5 | Whether the reconstruction/certification behavior persists in NSW | archive PCA map; raw reconstruction versus held-out contrast; full raw-reconstruction error ECDF | `nsw_archive_map_summary.csv`, `nsw_diagnostics_summary.csv`, `nsw_method_error_records.csv` |

The descriptive overview names remain for compatibility. The formal paper-facing
names are `figure2_synthetic_validation`, `figure3_selective_uncertainty`,
`figure4_rejection_bridge`, and `figure5_nsw`, each available as PNG and PDF.

The final presentation pass keeps Figure 4C as an evaluation-only mechanism
diagnostic and labels its log-scaled true-mechanism hull distance explicitly.
Figure 4D now shows only the greedy/ex-post-exhaustive value ratio; exact bridge
set-match rates remain in the saved optimality table rather than the main plot.
The NSW Table 3 analogue reports both all-target MAE and released-only MAE,
computed from the committed target-level records without rerunning simulation.

## Figure 3 B/D visual pass (2026-09-01)

This pass changes only the rendering of Panels B and D. The builder still reads
the committed `calibration_curve_summary.csv` and
`calibration_experiment_summary.csv`; no simulation or result-generation script
is called, and no numeric value is jittered or replaced.

- Panel B now connects each policy's four nominal levels in mean-width versus
  empirical-coverage space. Point annotations show `0.80`, `0.90`, `0.95`, and
  `0.975`; policy identity remains in the legend, with Honest ATLAS emphasized
  by the heavier blue trajectory. White-backed, tiered annotations reduce
  overlap among the coverage-one points.
- Panel D uses color and line style for policy and marker shape for scenario:
  circles denote strong mismatch and squares denote severe mismatch. Lines
  connect the two saved scenario records in strong-to-severe order. The exact
  no-rejection overlap at `(1, 1)` is retained and stated in the panel rather
  than hidden with coordinate jitter.

The prior paper-facing assets remain available through the repository history
and the legacy-layout files above; the prior Overleaf revision remains
available through Overleaf History.

## Appendix diagnostics

`appendix_certificate_diagnostic` preserves the 300-target synthetic
certificate-radius versus realized-error scatter for Appendix B.4.  
`appendix_nsw_certificate_diagnostic` preserves the NSW certificate-radius versus
reconstruction-error scatter for Appendix B.8.  These diagnostics are deliberately
separate from the main figures so that the main panels carry the claim-level
messages without dropping target-level audit evidence.

## Rollback

The original-layout assets remain under `results/figures/legacy_layout_*`. The
previous paper source remains available through Overleaf History for `test.tex`.
Restoring either the legacy assets or the previous Overleaf revision does not
modify the saved CSV/JSON records.
