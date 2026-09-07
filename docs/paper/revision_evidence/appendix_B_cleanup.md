# Appendix B revision and Overleaf cleanup audit

Final online source: `01_causal_atlas_bridge.tex`.
Overleaf project: https://www.overleaf.com/project/6a3410d137fc160e82dd884e

The online source was copied back through the editor and matched the archived source exactly.
XeLaTeX compilation: 54 pages, Errors 0, Warnings 0, Info 0.
The theory before Experiments and all of Appendix A match the pre-edit online backup.

## Revision

Appendix B now has five sections: protocols; robustness and failure boundaries; comparator and selection audit; real-data construction and stability; bridge evidence scope and stability.
It contains 15 tables (12 inline and three external inputs). Its former three external figures are no longer included.
The main experiments retain their structure. Five small text/reference repairs connect them to the reorganized appendix.
Results come from committed CSV records; this revision performs no experimental resampling.
Unfavorable comparisons and validity limitations are retained. The operational bridge monotonicity diagnosis is excluded.

## Cleanup scope

The lists below cover files actually observed in the Overleaf figures and tables folders, relative to `experiments/causal_atlas_bridge/`.
Not referenced means this compiled 01 document does not load the file, including nested inputs. The compiler log confirms the retained dependencies.
Some unused files contain results now summarized or embedded in 01. Their absence from the dependency list does not mean their experiments were discarded.
CSV records and old outputs may support reproduction or other documents. Keep the repository evidence when cleaning the Overleaf project. No files were deleted.
The 11 generated `app_b_*.tex` files exist locally for reproducibility; their content is embedded in 01 and these filenames were not present in the observed Overleaf folder.

## figures: keep (4)

```text
figure2_synthetic_validation.pdf
figure3_selective_uncertainty.pdf
figure4_rejection_bridge.pdf
figure5_nsw.pdf
```

## figures: not_referenced (15)

```text
appendix_certificate_diagnostic.pdf
appendix_nsw_certificate_diagnostic.pdf
extension_nsw_validation.pdf
figure2_composability.pdf
figure3_selective_uncertainty_v2.pdf
figure3_uncertainty.pdf
legacy_layout_nsw_validation.pdf
legacy_layout_nsw_validation.png
legacy_layout_synthetic_validation.pdf
legacy_layout_synthetic_validation.png
real_nsw_archive_validation.pdf
real_nsw_archive_validation.png
synthetic_atlas_validation.pdf
synthetic_atlas_validation.png
v1_figure5_nsw.pdf
```

## tables: keep (6)

```text
app_nsw_semisynthetic.tex
app_paired_comparison.tex
app_stronger_baselines.tex
main_nsw.tex
main_partial_id.tex
main_synthetic.tex
```

## tables: not_referenced (27)

```text
app_bridge_all_scenarios.tex
app_bridge_optimality.tex
app_bridge_retained.tex
app_calibration_levels.tex
app_certificate_components.tex
app_failure_boundary.tex
app_formal_nominal.tex
app_formal_stress_a.tex
app_formal_stress_b.tex
app_minimax.tex
app_nsw_calibration.tex
app_nsw_construction.tex
app_nsw_reference.tex
app_nsw_seedwise.tex
app_one_factor_sweeps.tex
app_partial_id_full.tex
app_representation_grid.tex
app_risk_coverage.tex
app_stronger_paired.tex
bridge_metrics.tex
main_synthetic_table.tex
nsw_local_contrasts.csv
real_metrics.csv
real_metrics.tex
synthetic_metrics.csv
synthetic_metrics.tex
synthetic_sensitivity.csv
```

## Evidence and reproduction

- `appendix_B_restructure.json`: source and CSV dependency hashes.
- `01_before_appendix_B_online.tex`: pre-edit online backup.
- `appendix_B_overleaf_compile_dom.txt`: observed final compiler log panel.
- `appendix_B_overleaf_inventory.json`: observed online file inventory.
- `appendix_B_asset_audit.json`: machine-readable cleanup decisions.
- Run `python scripts/build/restructure_appendix_b.py` to rebuild the appendix from CSV records.
- Run `python scripts/build/audit_appendix_b_assets.py` to reproduce this audit against the saved online observations.
