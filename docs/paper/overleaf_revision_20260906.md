# Overleaf Revision 2026-09-06

The final revision is live in Overleaf project
`6a3410d137fc160e82dd884e`, with `01_causal_atlas_bridge.tex` as the main
document. The authoritative source, compiled PDF, and all referenced assets are
archived in `docs/paper/overleaf/`.

## Source provenance and protected text

The merge started from the current online paper, downloaded after restoring the
6 September 02:15 Overleaf revision. An earlier local integration draft had an
older theory section and was briefly uploaded before the mismatch was detected.
That upload was reverted through Overleaf History before the experimental edits
were applied to the current online source. The obsolete upload ZIP was removed
from the live project; it is not a delivery artifact.

`docs/paper/revision_evidence/01_before_20260906.tex` preserves the online
baseline. Automated comparison confirms that the preamble, Introduction through
Main Results, Discussion, proof appendix, and references are identical to that
baseline. The abstract's theoretical claims are also unchanged; only its final
empirical claim was narrowed. No theory, assumption, theorem, or proof was edited.

The final source downloaded from Overleaf at 03:01 local time matches the local
source byte for byte, with SHA-256
`78daca4fd1694783f389e85b3969b78d3138e61d0900fb8a6315ffa460e1b062`.

## Experimental reporting

- Corrected the comparison in Section 6.2: ATLAS and no-rejection ATLAS share
  point weights, so their comparison measures selective release. No-rejection
  ATLAS versus semantic forced composition compares representations on all
  common targets.
- Added the release-rate Wilson 95% interval, `[0.408, 0.520]`, and released-MAE
  Monte Carlo SE, `0.007`, to the main synthetic results. They are calculated
  from the existing 300 target records, including 139 released targets.
- Added the bridge results across all four support scenarios and the
  semantic-planning inconsistency diagnostic to the main text.
- Distinguished the 90 paths per policy used for the budget-path visualization,
  the 300 paths per policy and scenario used for formal results, and the
  separate 30-repetition ex-post exhaustive comparison.
- Added the NSW construction and holdout counts to the main text: 50 neighbors,
  112 local objects, and 3 seeds times 20 splits times 28 holdouts, giving 1,680
  target evaluations. Clarified the restricted and enriched representation
  inputs.
- Kept the existing Appendix Figures 6 and 7 and experimental appendix. The
  main-text sequence remains composition, uncertainty, partial identification,
  bridge design, and NSW reconstruction.

## Figures and table layout

All paper assets use the requested directories:

```text
experiments/causal_atlas_bridge/figures/
experiments/causal_atlas_bridge/tables/
```

The final snapshot contains six figure PDFs and seventeen input tables.
Figures 3 and 4 were rebuilt from saved CSV/JSON records, with matching aliases
and updated hashes in `results/experiment_manifest.json`.

- Figure 3B: adjusted label offsets and plot limits to avoid annotation collisions.
- Figure 3D: changed the title to "Release and coverage under misspecification".
- Figure 4A: corrected the horizontal-axis label. The plotted field is
  `mean_oracle_hull_distance`, so the axis and caption now identify the mean
  distance to the true-mechanism archive hull. The previous target-shift
  parameter label did not describe the plotted quantity.
- NSW main table: locally set `tabcolsep` to `3.5pt`, fixing a 32.2851pt overfull
  box without changing any table values.

No new simulation draws, seed changes, parameter changes, or edited result CSVs
were introduced in this integration and visual correction pass.

## Validation

Overleaf compiled the final `01_causal_atlas_bridge.tex` with XeLaTeX and TeX
Live 2025. Build `1a072e2f107-e629bddfcc4c77f2` produced 53 pages at
2026-09-05 18:44 UTC (2026-09-06 02:44 Asia/Shanghai).

- Overleaf diagnostic counters: All logs 0, Errors 0, Warnings 0, Info 0.
- Raw compiler log: `docs/paper/revision_evidence/overleaf_compile.log`.
  No compiler warning, error, overfull box, or underfull box was found.
- `python scripts/build/verify_overleaf_revision.py` passed: protected text,
  all 23 assets, reference labels, shared-target statistics, and compiler log.
- `python -m unittest discover -s tests -p test_paper_figures.py`: 6 tests passed.
- Rendered PDF pages 16, 17, 19, 20, 21, 46, and 51 were inspected for figure
  labels, captions, table widths, and the relevant experimental text.

Hashes and numerical audit results are stored in
`docs/paper/revision_evidence/source_and_results_audit.json`.
The final compile was performed in Overleaf; the local minimal TinyTeX
installation lacks `mathtools` and was not used to certify the final PDF.

## Interpretation limits

The NSW evaluation remains a descriptive reconstruction stress test against
noisy held-out contrasts. Overlapping neighborhoods create dependence, and the
protocol does not implement full shared-unit covariance correction. Reference
inclusion is not causal-effect coverage. These revisions do not establish
subgroup causal ground truth or external generalization.
